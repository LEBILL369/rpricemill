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
				frappe.throw('Phone Number already linked to Contact: ' + get_link_to_form('Contact', con_parent))
						
def update_loyality(doc,action):
	loyalty = frappe.get_doc("Customer", doc.customer)
	if(loyalty.loyalty_program):
		if_loyalty = frappe.get_doc("Loyalty Program", loyalty.loyalty_program)
	value = 0
	if(if_loyalty.loyalty_program_based_on_item == 1):
		for ele in range(len(doc.items)):
			item = frappe.get_doc("Item",doc.items[ele].item_code)
			if(item.loyalty_point):
				value += (int(item.loyalty_point) * int(item.valuation_boost)) * int(doc.items[ele].qty)
	point_entry = frappe.db.sql("select name from `tabLoyalty Point Entry` where invoice = %s",(doc.name))
	if(len(point_entry)):
		if(doc.redeem_loyalty_points == 0):
			val_point = frappe.get_doc("Loyalty Point Entry",point_entry[0][0])
			val_point.loyalty_points = value
			# frappe.db.set_value("Loyalty Point Entry",point_entry[0][0],"")
			val_point.save(ignore_permissions=True)

@frappe.whitelist()
def get_current_balance(company,mode_of_pay,idx):
	doc = frappe.db.sql("""select mpa.default_account from `tabMode of Payment` as mp inner join `tabMode of Payment Account` as mpa on mpa.parent = mp.name where mpa.company = %s and mp.name = %s""",(company,mode_of_pay))
	if(len(doc)):
		current_balance = get_balance_on(account = doc[0][0],company = company)
		return(current_balance,int(idx))


@frappe.whitelist()
def get_customer_data(customer):
	doc = frappe.get_doc("Customer",customer)
	info = get_dashboard_info(doc.doctype, doc.name, doc.loyalty_program)
	return(info)

@frappe.whitelist()
def get_account(company):
	doc = frappe.get_doc("Company",company)
	return(doc.loyalty_redemption_expense_account)