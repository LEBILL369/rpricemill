from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import comma_and,get_link_to_form
from erpnext.accounts.utils import get_balance_on
from erpnext.accounts.party import  get_dashboard_info
from frappe.model.naming import parse_naming_series
from erpnext.accounts.utils import get_fiscal_year
from datetime import datetime, timedelta
from frappe.utils import  get_link_to_form

def rice_allert(doc,action):
	count = frappe.db.sql("""select count(*)
							from (
							        select sales.name,
							            sales.posting_date,
							            item.item_code,
							            sales.customer,
							            item.item_group
							        from (
							                SELECT si.name,
							                    si.posting_date,
							                    sit.item_code,
							                    si.customer
							                from `tabSales Invoice` as si
							                    inner join `tabSales Invoice Item` as sit on sit.parent = si.name
							            ) as sales
							            inner join `tabItem` as item on item.name = sales.item_code
							    ) as grp
							    inner join `tabItem Group` as igrp on grp.item_group = igrp.name
							WHERE grp.posting_date BETWEEN date_sub(curdate(), INTERVAL 10 DAY)
							    and curdate()
							    and grp.customer = %s
							    and igrp.rp_item_group_primary like %s""",(doc.customer,"Rice"))
	if not count[0][0]:
		frappe.msgprint("Customer did not buy any item of group Rice")


def pos_batch(doc,action):
	if(doc.pos_profile):
		branch = frappe.get_value("POS Profile",{"name" : doc.pos_profile},"branch")
		if branch:
			if not doc.branch:
				doc.branch = branch
			for item in doc.items:
				if not item.branch:
					item.branch = branch
			for tax in doc.taxes:
				if not tax.branch:
					tax.branch = branch
		else:
			frappe.throw("Branch Not Available in POS Profile")


def contact_before_save(doc, action):
	nos = []
	for num in doc.phone_nos:
		if frappe.db.exists('Contact Phone', {'phone': num.phone}):
			con_parent = frappe.db.get_value('Contact Phone', {'phone': num.phone}, 'parent')
			if con_parent == doc.name:
				if num.phone in nos:
					frappe.throw('Contact already in the list')
				else:
					nos.append(num.phone)
			else:
				link_name = frappe.db.get_value('Dynamic Link', {'link_doctype': 'Customer', 'parenttype': 'Contact', 'parent': con_parent}, 'link_name')
				if link_name:
					frappe.throw('Phone Number already linked to Customer: ' + get_link_to_form('Customer', link_name))
				else:
					frappe.throw('Phone Number already linked to Contact: ' + get_link_to_form('Contact', link_name))
						
def update_loyality(doc,action):
	loyalty = frappe.get_doc("Customer", doc.customer)
	value = 0
	if(loyalty.loyalty_program):
		if_loyalty = frappe.get_doc("Loyalty Program", loyalty.loyalty_program)
		if(if_loyalty.loyalty_program_based_on_item == 1):
			for ite in doc.items:
				if frappe.db.exists('Item', ite.item_code):
					item = frappe.get_doc("Item", ite.item_code)
					if(item.loyalty_points > 0):
						value += (float(item.loyalty_points) * float(item.loyalty_points_booster)) * int(ite.qty)
		point_entry = frappe.db.sql("select name from `tabLoyalty Point Entry` where invoice = %s and redeem_against is null",(doc.name))
		if(len(point_entry)):
			val_point = frappe.get_doc("Loyalty Point Entry",point_entry[0][0])
			val_point.loyalty_points = value
			val_point.save(ignore_permissions=True)
			new_customer = frappe.db.sql("""select count(*) from `tabSales Invoice` where customer = %s""",(doc.customer))
			if new_customer[0][0] == 1:
				refrel_value = value / 2
				ref_customer = frappe.get_value("Customer",{"name":doc.customer},"referred_customer")
				if ref_customer:
					frappe.get_doc({
						"doctype" : "Loyalty Point Entry",
						"loyalty_program" : val_point.loyalty_program,
						"loyalty_program_tier" : val_point.loyalty_program_tier,
						"customer" : ref_customer,
						"loyalty_points" : refrel_value,
						"expiry_date" : val_point.expiry_date,
						"posting_date": val_point.posting_date,
						"company" : val_point.company
					}).save(ignore_permissions = True)


	data_points = get_dashboard_info('Customer', doc.customer)
	outstanding = 0
	for data_point in data_points:
		if data_point['total_unpaid']:
			outstanding += data_point['total_unpaid']
	if outstanding and doc.doctype == 'POS Invoice':
		customer_name = frappe.db.get_value('Customer', doc.customer, 'customer_name')
		frappe.msgprint(get_link_to_form('Customer', doc.customer) + " - " + customer_name + " has an outstanding of " + str(outstanding))

@frappe.whitelist()
def update_loyalty_account(doc, action):
	if(doc.redeem_loyalty_points == 1):
		redeem_amount = 0
		for item in doc.items:
			if(frappe.get_value("Item",item.item_code,'eligible_for_redeem')):
				redeem_amount += item.amount
		if(redeem_amount < doc.loyalty_amount ):
			frappe.throw("Loyalty points can only be used to redeem the eligible items.")
		acc = frappe.db.get_value('Company', doc.company, 'loyalty_redemption_expense_account')
		cost_center = frappe.db.get_value('Company', doc.company, 'cost_center')
		if not doc.loyalty_redemption_account:
			doc.loyalty_redemption_account = acc
		if not doc.loyalty_redemption_cost_center:
			doc.loyalty_redemption_cost_center = cost_center

@frappe.whitelist()
def get_all_balances(pos_profile):
	payments = frappe.db.get_list('POS Payment Method', {'parent': pos_profile}, 'mode_of_payment')
	company = frappe.db.get_value('POS Profile', pos_profile, 'company')
	res = {}
	for payment in payments:
		if payment.mode_of_payment:
			balance, idx = get_current_balance(company, payment.mode_of_payment, 0)
			res[payment.mode_of_payment] = balance
	return res


@frappe.whitelist()
def get_current_balance(company,mode_of_pay,idx):
	doc = frappe.db.sql("""select mpa.default_account from `tabMode of Payment` as mp inner join `tabMode of Payment Account` as mpa on mpa.parent = mp.name where mpa.company = %s and mp.name = %s""",(company,mode_of_pay))
	if(len(doc)):
		current_balance = get_balance_on(account = doc[0][0],company = company, ignore_account_permission=True)
		return(current_balance,int(idx))


@frappe.whitelist()
def get_customer_data(customer,company):
	if customer:
		doc = frappe.get_doc("Customer",customer)
		data_points = get_dashboard_info(doc.doctype, doc.name, doc.loyalty_program)
		res = {
			'total_unpaid': 0,
			'billing_this_year': 0,
			'info': '',
			'loyalty_points': 0
		}
		for data_point in data_points:
			if data_point['total_unpaid']:
				res['total_unpaid'] += data_point['total_unpaid']
			if data_point['billing_this_year']:
				res['billing_this_year'] += data_point['billing_this_year']
			if 'loyalty_points' not in data_point:
				data_point['loyalty_points'] = 0
			if 'loyalty_points' in data_point:
				if company == data_point["company"]:
					res['loyalty_points'] = data_point['loyalty_points']
			res['info'] += f"Company: {data_point['company']}, \n Outstanding: {data_point['total_unpaid']}, \n Turn Over: {data_point['billing_this_year']}, \n Loyalty Points: {data_point['loyalty_points']} \n\n"
		return res

@frappe.whitelist()
def get_account(company):
	doc = frappe.get_doc("Company",company)
	return(doc.loyalty_redemption_expense_account)

def save_customer(doc,action):
	for links in doc.links:
		if(links.link_doctype == "Customer"):
			customer = frappe.get_doc("Customer",links.link_name)
			customer.save()

def add_mobile_search(doc, action):
	phone_numbers = frappe.db.sql("""select group_concat(phone.phone) as all_numbers from tabCustomer as customer inner join
																		`tabContact Phone` as phone
																		inner join `tabContact` as contact on contact.name = phone.parent
																		inner join `tabDynamic Link` as dl on dl.link_doctype = 'Customer' and dl.parenttype = 'Contact'
																		and dl.link_name = customer.name and dl.parent = contact.name
																		where customer.name = %s
																		group by phone.phone""", doc.name, as_dict = 1)
	number_ = ""
	if len(phone_numbers):
		for number in range(len(phone_numbers)):
			if 'all_numbers' in phone_numbers[number]:
				number_ += phone_numbers[number]['all_numbers']
			if(number != len(phone_numbers) - 1):
				number_  += ","
	doc.mobile_search = number_

def add_vehicle_log(doc, action):
	if doc.delivering_driver and doc.vehicle and (doc.current_odometer_value or doc.return_odometer_value):
		vehicle_log = frappe.new_doc('Vehicle Log')
		vehicle_log.license_plate = doc.vehicle
		vehicle_log.employee = frappe.db.get_value('Driver', doc.delivering_driver, 'employee')
		if doc.return_odometer_value:
			vehicle_log.odometer = doc.return_odometer_value
		elif doc.current_odometer_value:
			vehicle_log.odometer = doc.current_odometer_value
		vehicle_log.date = doc.posting_date
		vehicle_log.purpose = 'Sales Delivery'
		vehicle_log.remarks = doc.name
		vehicle_log.save()
		vehicle_log.submit()
def get_fiscal_year_short_form():
	fy =  frappe.db.get_single_value('Global Defaults', 'current_fiscal_year')
	return fy.split('-')[0][2:]



def name_sales_invoice(doc, action):
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	fy = get_fiscal_year_short_form()
	if doc.is_pos:
		doc.name = parse_naming_series(f'{abbr}POSI{fy}-.######')
	else:
		doc.name = parse_naming_series(f'{abbr}SI{fy}-.######')
	
def name_sales_order(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}SO{fy}-.######")

def name_purchase_order(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}PO{fy}-.######")

def name_purchase_invoice(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}PI{fy}-.######")

def name_purchase_receipt(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}PR{fy}-.######")

def name_payment_entry(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}PAY{fy}-.######")

def name_pos_invoice(doc, action):
	fy = get_fiscal_year_short_form()
	abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
	doc.name = parse_naming_series(f"{abbr}POI{fy}-.######")

def get_gstno(doc,action):
	gstin = frappe.get_value("Address",{"name" : doc.customer_address},['gstin'])
	if gstin:
		doc.gst_no = " "
	elif doc.tax_id:
		doc.gst_no = doc.tax_id
	else:
		doc.gst_no = "  "
	if(doc.total_unpaid):
		doc.outstanding_pf = doc.total_unpaid
	else:
		data = 	get_customer_data(doc.customer,doc.company)
		doc.outstanding_pf = data["total_unpaid"]
	phone = frappe.db.sql("""select cp.phone from `tabContact Phone` as cp inner join (select con.name as conname from `tabContact` as con inner join `tabDynamic Link` as dl on dl.parent = con.name where dl.link_name = %s) as con on con.conname = cp.parent""",(doc.customer),as_list = 1)
	number = ""
	for no in range(len(phone)):
		number += phone[no][0]
		if(no != len(phone) - 1):
			number += "," 
	doc.mobile = number
def scgst(doc,action):
	for items in doc.items:
		if items.item_tax_template:
			sgst = 0
			cgst = 0
			tax = frappe.db.sql("""select ttd.tax_type,ttd.tax_rate from `tabItem Tax Template` as tt inner join `tabItem Tax Template Detail` as ttd on tt.name = ttd.parent where tt.name = %s""",(items.item_tax_template),as_dict = 1)
			for _tax in tax:
				data = _tax["tax_type"]
				data = data.split(" - ")
				if("SGST" in data):
					sgst = _tax["tax_rate"]
				elif("CGST" in data):
					cgst = _tax["tax_rate"]
				if sgst and cgst :
					break
			rate = cgst + sgst
			items.sgst = round((items.amount - (items.amount/(1 + (float(rate)/100))))/2,2)
			items.cgst = round((items.amount - (items.amount/(1 + (float(rate)/100))))/2,2)

		else:
			items.sgst = 0
			items.cgst = 0
@frappe.whitelist()
def get_address(store_branch):
	return(frappe.get_value("Address",{"store_branch" : store_branch},'name'))

@frappe.whitelist()
def get_mobile_number(customer):
	return(frappe.get_value("Customer",{"name" : customer},'mobile_no'))


@frappe.whitelist()
def create_events_from_vehicle_remainder(doc, action):
	if doc.remainders:
		for prop in doc.remainders:
			if frappe.db.exists('Event', {'vehicle': doc.name, 'remainder_property': prop.property}):
				exisiting_event = frappe.get_doc('Event', {'vehicle': doc.name, 'remainder_property': prop.property})
				if prop.remind_before_in_days:
					start = datetime.combine(datetime.strptime(prop.date, '%Y-%m-%d') - timedelta(days=prop.remind_before_in_days), datetime.min.time())
				else:
					start = datetime.combine(datetime.strptime(prop.date, '%Y-%m-%d'), datetime.min.time())
				if prop.assign_to:
					is_present = 0
					for participant in exisiting_event.event_participants:
						if participant.reference_docname == prop.assign_to:
							is_present = 1
							break
					if not is_present:
						exisiting_event.append("event_participants", {
							"reference_doctype": 'Employee',
							"reference_docname": prop.assign_to,
						})
				exisiting_event.starts_on = start
				exisiting_event.status = 'Open'
				exisiting_event.all_day = 1
				if prop.is_recurring:
					exisiting_event.repeat_this_event = 1
					exisiting_event.repeat_on = prop.repeat_on
					exisiting_event.repeat_till = prop.repeat_till
				else:
					exisiting_event.repeat_this_event = 0
				exisiting_event.description = prop.remarks
				exisiting_event.save(ignore_permissions=True)
			else:
				event = frappe.new_doc('Event')
				event.subject = doc.name + ' - ' + prop.property
				event.event_category = 'Event'
				event.event_type = 'Private'
				event.vehicle = doc.name
				event.remainder_property = prop.property
				if prop.remind_before_in_days:
					start = datetime.combine(datetime.strptime(prop.date, '%Y-%m-%d') - timedelta(days=prop.remind_before_in_days), datetime.min.time())
				else:
					start = datetime.combine(datetime.strptime(prop.date, '%Y-%m-%d'), datetime.min.time())

				if prop.assign_to:
					event.append("event_participants", {
						"reference_doctype": 'Employee',
						"reference_docname": prop.assign_to,
					})
				event.starts_on = start
				event.status = 'Open'
				event.all_day = 1
				if prop.is_recurring:
					event.repeat_this_event = 1
					event.repeat_on = prop.repeat_on
					event.repeat_till = prop.repeat_till
				else:
					event.repeat_this_event = 0
				event.description = prop.remarks
				event.save(ignore_permissions=True)

@frappe.whitelist()
def pos_qty(value,doc):
	qty = 0
	for item in doc.items:
		qty += float(item.qty)
	return(qty)

@frappe.whitelist()
def get_sales_summary(company,pos_profile):
	date_ = datetime.now()
	date_ = date_.date()
	str_date = str(date_)
	_date = datetime.strptime(str_date,"%Y-%m-%d")
	existing_customer = frappe.db.sql("""select count(si.name) as count,sum(grand_total) as sales from `tabSales Invoice` as si inner join `tabCustomer` as cos on cos.name = si.customer where si.posting_date = %s and si.company = %s and cos.creation < %s and si.pos_profile = %s""",(date_,company,_date,pos_profile),as_dict = 1)
	new_customer = frappe.db.sql("""select count(si.name) as count,sum(grand_total) as sales from `tabSales Invoice` as si inner join `tabCustomer` as cos on cos.name = si.customer where si.posting_date = %s and si.company = %s and cos.creation >= %s and si.pos_profile = %s""",(date_,company,_date,pos_profile),as_dict = 1)
	# outstanding = frappe.db.sql("""select count(si.name) as count,sum(outstanding_amount) as sales from `tabSales Invoice` as si inner join `tabCustomer` as cos on cos.name = si.customer where si.posting_date = %s and si.company = %s and cos.creation >= %s and  si.outstanding_amount > %s""",(date_,company,_date,"0"),as_dict = 1)
	total_count = 0
	total_sales = 0
	final_result = []
	if len(existing_customer):
		existing_customer = existing_customer[0].update({"particular": "Existing Customer"})
		if existing_customer["count"]:
			total_count += int(existing_customer["count"])
		if existing_customer["sales"]:
			total_sales += float(existing_customer["sales"])
		else:
			existing_customer["sales"] = 0 
		final_result.append(existing_customer)
	if len(new_customer):
		new_customer = new_customer[0].update({"particular": "New Customer"})
		if new_customer["count"]:
			total_count += int(new_customer["count"])
		if new_customer["sales"]:
			total_sales += float(new_customer["sales"])
		else:
			new_customer["sales"] = 0 
		final_result.append(new_customer)
	# if len(outstanding):
	# 	outstanding = outstanding[0].update({"particular": "Outstanding"})
	# 	if not outstanding["sales"]:
	# 		outstanding["sales"] = 0 
	# 	final_result.append(outstanding)
	final_result.append({"particular": "Total","count":total_count,"sales":total_sales})
	return(final_result)

@frappe.whitelist()
def get_target_summary(company,pos_profile,posting_date):
	print(pos_profile)
	starting_date = posting_date.split("-")
	starting_date[2] = "01" 
	starting_date = starting_date[0] + "-" + starting_date[1] + "-" + starting_date[2] 
	starting_date = datetime.strptime(starting_date,"%Y-%m-%d").date()
	posting_date = datetime.strptime(posting_date,"%Y-%m-%d").date()
	annual = frappe.db.sql("""select sum(grand_total) from `tabSales Invoice` where company = %s and pos_profile = %s""",(company,pos_profile))
	monthly = frappe.db.sql("""select sum(grand_total) from `tabSales Invoice` where company = %s and pos_profile = %s and posting_date between %s and %s""",(company,pos_profile,starting_date,posting_date))
	branch = frappe.get_value("POS Profile",{"name": pos_profile},"branch")
	print(branch)
	target = frappe.get_list("Branch",{"name" : branch},['monthly_target','annual_target_'])
	print(target)
	print(annual)

	target_summary = []
	target_summary.append({"target":"Monthly","target_amount" : target[0]["monthly_target"],"sales_amount" : monthly[0][0]})
	target_summary.append({"target":"Annual","target_amount" : target[0]["annual_target_"],"sales_amount" : annual[0][0]})
	print(target_summary)
	return(target_summary)

@frappe.whitelist()
def get_recent_items_from_pos(filters,fields,limit):
	value = frappe.db.sql("""select chld.branch as branch,
								    chld.name as name,
								    chld.grand_total as grand_total,
								    chld.posting_date as posting_date,
								    chld.creation,
								    chld.posting_time as posting_time,
								    chld.currency as currency,
								    chld.status as status,
								    chld.day_count as day_count,
								    cpy.abbr as abbrivation
								from `tabCompany` as cpy
								    inner join (
								        select ifnull(
								                concat("  (", sit.branch, ")"),
								                concat("  (", sit.warehouse, ")")
								            ) as branch,
								            sit.item_name as name,
								            sit.amount as grand_total,
								            si.posting_date,
								            si.creation,
								            si.posting_time,
								            si.price_list_currency as currency,
								            concat(FORMAT(sit.qty, 2), ' QTY') as status,
								            CONCAT(
								                DATEDIFF(CURDATE(), si.posting_date),
								                ' Days ago'
								            ) as day_count,
								            si.company,
								            si.customer
								        from `tabSales Invoice` as si
								            inner join `tabSales Invoice Item` as sit on sit.parent = si.name
								        WHERE si.docstatus = '1'
								    ) as chld on chld.company = cpy.name
								where chld.customer = %s
								order by chld.creation desc
								limit 20""",(filters),as_dict = 1)
	return(value)