from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import comma_and,get_link_to_form
from erpnext.accounts.utils import get_balance_on
from erpnext.accounts.party import  get_dashboard_info

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
				item = frappe.get_doc("Item", ite.item_code)
				if(item.loyalty_points):
					value += (int(item.loyalty_points) * int(item.loyalty_points_booster)) * int(ite.qty)
		point_entry = frappe.db.sql("select name from `tabLoyalty Point Entry` where invoice = %s and redeem_against is null",(doc.name))
		if(len(point_entry)):
			val_point = frappe.get_doc("Loyalty Point Entry",point_entry[0][0])
			val_point.loyalty_points = value
			# frappe.db.set_value("Loyalty Point Entry",point_entry[0][0],"")
			val_point.save()

@frappe.whitelist()
def update_loyalty_account(doc, action):
	if(doc.redeem_loyalty_points == 1):
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
		current_balance = get_balance_on(account = doc[0][0],company = company)
		return(current_balance,int(idx))


@frappe.whitelist()
def get_customer_data(customer):
	if customer:
		doc = frappe.get_doc("Customer",customer)
		data_points = get_dashboard_info(doc.doctype, doc.name, doc.loyalty_program)
		res = {
			'total_unpaid': 0,
			'billing_this_year': 0,
			'info': ''
		}
		for data_point in data_points:
			if data_point['total_unpaid']:
				res['total_unpaid'] += data_point['total_unpaid']
			if data_point['billing_this_year']:
				res['billing_this_year'] += data_point['billing_this_year']
			if not data_point['loyalty_points']:
				data_point['loyalty_points'] = 0
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
