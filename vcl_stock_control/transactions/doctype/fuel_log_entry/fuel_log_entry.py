import frappe
from frappe.model.document import Document


class FuelLogEntry(Document):
    def validate(self):
        self.validate_quantities()
        self.set_opening_balance()
        self.calculate_closing_balance()
        if self.transaction_type == "Issue" and self.issue_to == "Vehicle":
            self.fetch_previous_vehicle_entry()
            self.calculate_consumption()
            self.set_consumption_flag()

    def on_submit(self):
        pass  # Future: could trigger alerts

    def on_cancel(self):
        pass  # Future: could recalculate downstream balances

    def validate_quantities(self):
        if self.transaction_type == "Issue":
            if not self.qty_issued or self.qty_issued <= 0:
                frappe.throw("Litres Issued must be greater than zero.")
            if self.issue_to == "Vehicle":
                if not self.vehicle:
                    frappe.throw("Vehicle is required when Issue To is Vehicle.")
                if not self.driver:
                    frappe.throw("Driver is required when Issue To is Vehicle.")
                if not self.km_before_fueling or self.km_before_fueling <= 0:
                    frappe.throw("KM Before Fueling is required and must be greater than zero.")
            elif not self.issue_to:
                frappe.throw("Issue To is required for issuance entries.")
            elif self.issue_to != "Vehicle" and not self.purpose_description:
                frappe.throw("Purpose / Equipment is required for non-vehicle issuances.")
            # Clear receipt fields
            self.qty_received = 0
            self.supplier_name = ""
            self.delivery_reference = ""

        elif self.transaction_type == "Receive":
            if not self.qty_received or self.qty_received <= 0:
                frappe.throw("Litres Received must be greater than zero.")
            # Clear issuance fields
            self.qty_issued = 0
            self.issue_to = ""
            self.vehicle = ""
            self.vehicle_plate = ""
            self.driver = ""
            self.driver_name = ""
            self.km_before_fueling = 0
            self.previous_km = 0
            self.km_since_last_fill = 0
            self.previous_litres = 0
            self.km_per_litre = 0
            self.consumption_flag = ""
            self.purpose_description = ""

    def set_opening_balance(self):
        """
        Auto-fetch the closing balance of the most recent SUBMITTED
        Fuel Log Entry (for the same site) as this entry's opening balance.

        If no previous entry exists (very first entry), require manual input
        or default to 0.
        """
        previous = frappe.db.sql("""
            SELECT closing_balance
            FROM `tabFuel Log Entry`
            WHERE docstatus = 1
              AND site = %(site)s
              AND (posting_date < %(posting_date)s
                   OR (posting_date = %(posting_date)s AND posting_time < %(posting_time)s))
            ORDER BY posting_date DESC, posting_time DESC
            LIMIT 1
        """, {
            "site": self.site,
            "posting_date": self.posting_date,
            "posting_time": self.posting_time
        }, as_dict=True)

        if previous:
            self.opening_balance = previous[0].closing_balance
        elif not self.opening_balance:
            frappe.throw(
                "No previous Fuel Log Entry found for this site. "
                "Please enter the Opening Balance manually for the first entry."
            )

    def calculate_closing_balance(self):
        """closing = opening - issued + received"""
        issued = self.qty_issued or 0
        received = self.qty_received or 0
        self.closing_balance = self.opening_balance - issued + received

        if self.closing_balance < 0:
            frappe.msgprint(
                f"Warning: Closing balance is negative ({self.closing_balance} L). "
                "Please verify the quantities.",
                indicator="orange",
                alert=True
            )

    def fetch_previous_vehicle_entry(self):
        """
        Find the most recent submitted Fuel Log Entry for the same vehicle
        to get previous KM reading and litres issued.
        """
        if not self.vehicle:
            return

        previous = frappe.db.sql("""
            SELECT km_before_fueling, qty_issued
            FROM `tabFuel Log Entry`
            WHERE docstatus = 1
              AND transaction_type = 'Issue'
              AND issue_to = 'Vehicle'
              AND vehicle = %(vehicle)s
              AND name != %(name)s
              AND (posting_date < %(posting_date)s
                   OR (posting_date = %(posting_date)s AND posting_time < %(posting_time)s))
            ORDER BY posting_date DESC, posting_time DESC
            LIMIT 1
        """, {
            "vehicle": self.vehicle,
            "name": self.name or "",
            "posting_date": self.posting_date,
            "posting_time": self.posting_time
        }, as_dict=True)

        if previous:
            self.previous_km = previous[0].km_before_fueling
            self.previous_litres = previous[0].qty_issued
        else:
            self.previous_km = 0
            self.previous_litres = 0

    def calculate_consumption(self):
        """
        Calculate KM since last fill and KM per litre.

        The KM per litre measures the efficiency of the PREVIOUS fill:
        - Distance = current KM - previous KM (distance travelled on previous fuel)
        - Efficiency = distance / previous litres issued
        """
        if self.previous_km and self.km_before_fueling and self.previous_km > 0:
            self.km_since_last_fill = self.km_before_fueling - self.previous_km

            if self.km_since_last_fill < 0:
                frappe.msgprint(
                    f"Warning: Current KM ({self.km_before_fueling}) is less than "
                    f"previous KM ({self.previous_km}). Please verify the odometer reading.",
                    indicator="orange",
                    alert=True
                )
                self.km_per_litre = 0
            elif self.previous_litres and self.previous_litres > 0:
                self.km_per_litre = round(self.km_since_last_fill / self.previous_litres, 2)
            else:
                self.km_per_litre = 0
        else:
            self.km_since_last_fill = 0
            self.km_per_litre = 0

    def set_consumption_flag(self):
        """
        Flag abnormal fuel consumption.

        Thresholds (configurable — adjust based on VCL fleet data):
        - Normal: >= 5 km/L
        - Warning: 3 to 5 km/L (higher than expected consumption)
        - Critical: < 3 km/L (possible theft, leak, or mechanical issue)

        Only flag if we have valid comparison data (not first entry for vehicle).
        """
        if not self.km_per_litre or self.km_per_litre <= 0:
            self.consumption_flag = ""
            return

        if self.km_per_litre >= 5:
            self.consumption_flag = "Normal"
        elif self.km_per_litre >= 3:
            self.consumption_flag = "Warning"
            frappe.msgprint(
                f"Fuel consumption warning for {self.vehicle}: "
                f"{self.km_per_litre} km/L (expected >= 5 km/L). "
                f"Distance: {self.km_since_last_fill} km on {self.previous_litres} L.",
                indicator="orange",
                alert=True
            )
        else:
            self.consumption_flag = "Critical"
            frappe.msgprint(
                f"CRITICAL: Abnormal fuel consumption for {self.vehicle}: "
                f"{self.km_per_litre} km/L (expected >= 5 km/L). "
                f"Distance: {self.km_since_last_fill} km on {self.previous_litres} L. "
                "Possible theft, leak, or mechanical issue. Please investigate.",
                indicator="red",
                alert=True
            )
