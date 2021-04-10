from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import comma_and,get_link_to_form
from erpnext.accounts.utils import get_balance_on
from erpnext.accounts.party import  get_dashboard_info
from frappe.model.naming import parse_naming_series
from erpnext.accounts.utils import get_fiscal_year

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
			# frappe.db.set_value("Loyalty Point Entry",point_entry[0][0],"")
			val_point.save(ignore_permissions=True)

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


def add_mobile_search(doc, action):
	phone_numbers = frappe.db.sql("""select group_concat(phone.phone) as all_numbers from tabCustomer as customer inner join
																		`tabContact Phone` as phone
																		inner join `tabContact` as contact on contact.name = phone.parent
																		inner join `tabDynamic Link` as dl on dl.link_doctype = 'Customer' and dl.parenttype = 'Contact'
																		and dl.link_name = customer.name and dl.parent = contact.name
																		where customer.name = %s
																		group by phone.phone""", doc.name, as_dict = 1)
	if len(phone_numbers):
		if 'all_numbers' in phone_numbers[0]:
			doc.mobile_search = phone_numbers[0]['all_numbers']

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

@frappe.whitelist()
def get_address(store_branch):
	return(frappe.get_value("Address",{"store_branch" : store_branch},'name'))