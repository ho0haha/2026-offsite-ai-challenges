import uuid
import datetime


def process_order(order_data: dict) -> dict:
    # validate order data
    r = {}
    if order_data is not None:
        if isinstance(order_data, dict):
            if "items" in order_data:
                if isinstance(order_data["items"], list):
                    if len(order_data["items"]) > 0:
                        # check customer id
                        if "customer_id" in order_data:
                            if isinstance(order_data["customer_id"], str):
                                if len(order_data["customer_id"]) > 0:
                                    cid = order_data["customer_id"]
                                else:
                                    raise ValueError("Customer ID cannot be empty")
                            else:
                                raise ValueError("Customer ID must be a string")
                        else:
                            raise ValueError("Missing customer_id")
                    else:
                        raise ValueError("Order must have at least one item")
                else:
                    raise ValueError("Items must be a list")
            else:
                raise ValueError("Missing items in order")
        else:
            raise ValueError("Order data must be a dictionary")
    else:
        raise ValueError("Order data cannot be None")

    # extra validation for item structure
    for i in range(len(order_data["items"])):
        it = order_data["items"][i]
        if not isinstance(it, dict):
            raise ValueError("Each item must be a dictionary")
        if "name" not in it:
            raise ValueError("Item missing name field")
        if not isinstance(it["name"], str):
            raise ValueError("Item name must be a string")
        if len(it["name"]) == 0:
            raise ValueError("Item name cannot be empty")
        if len(it["name"]) > 100:
            raise ValueError("Item name too long")
        # check for weird characters
        for c in it["name"]:
            if not c.isalnum() and c != " " and c != "-" and c != "'":
                raise ValueError("Item name contains invalid characters: " + it["name"])

    # TODO: add database lookup later
    # TODO: refactor this function someday
    # NOTE: this works, don't touch it
    # HACK: prices are hardcoded because the database was too slow

    # menu prices - just hardcoded here
    p = {}
    p["Burger"] = 8.99
    p["Cheeseburger"] = 9.99
    p["Veggie Burger"] = 9.49
    p["Fries"] = 3.99
    p["Large Fries"] = 5.49
    p["Onion Rings"] = 4.99
    p["Soda"] = 1.99
    p["Large Soda"] = 2.99
    p["Milkshake"] = 5.99
    p["Water"] = 0.99
    p["Salad"] = 7.99
    p["Chicken Wrap"] = 8.49
    p["Fish Tacos"] = 10.99
    p["Ice Cream"] = 3.49
    p["Coffee"] = 2.49
    p["Lemonade"] = 2.49

    # validate each item and calculate subtotal
    items_result = []
    st = 0.0
    tq = 0
    for i in range(len(order_data["items"])):
        it = order_data["items"][i]
        if isinstance(it, dict):
            if "name" in it:
                if it["name"] in p:
                    if "quantity" in it:
                        if isinstance(it["quantity"], int):
                            if it["quantity"] > 0:
                                if it["quantity"] <= 99:
                                    # calculate price for this item
                                    ip = p[it["name"]]
                                    q = it["quantity"]
                                    tp = ip * q

                                    # bulk discount - 10% off if 5+ of same item
                                    if q >= 5:
                                        tp = tp * 0.9
                                        items_result.append({
                                            "name": it["name"],
                                            "quantity": q,
                                            "unit_price": ip,
                                            "total_price": round(tp, 2),
                                            "discount_applied": "bulk_10_percent"
                                        })
                                    else:
                                        items_result.append({
                                            "name": it["name"],
                                            "quantity": q,
                                            "unit_price": ip,
                                            "total_price": round(tp, 2),
                                            "discount_applied": None
                                        })

                                    st = st + round(tp, 2)
                                    tq = tq + q
                                else:
                                    raise ValueError("Quantity cannot exceed 99 for item: " + it["name"])
                            else:
                                raise ValueError("Quantity must be positive for item: " + it["name"])
                        else:
                            raise ValueError("Quantity must be an integer for item: " + it["name"])
                    else:
                        raise ValueError("Missing quantity for item: " + it["name"])
                else:
                    raise ValueError("Unknown menu item: " + it["name"])
            else:
                raise ValueError("Item missing name field")
        else:
            raise ValueError("Each item must be a dictionary")

    # combo detection and discount
    # Combo 1: Burger (any) + Fries (any) + Drink (any soda/water/lemonade) = 15% off the combo items
    # Combo 2: Chicken Wrap + Salad + Drink = 10% off the combo items
    combo_discount = 0.0
    has_burger = False
    has_fries = False
    has_drink = False
    has_wrap = False
    has_salad = False
    has_drink2 = False

    for it in items_result:
        if it["name"] == "Burger" or it["name"] == "Cheeseburger" or it["name"] == "Veggie Burger":
            has_burger = True
        if it["name"] == "Fries" or it["name"] == "Large Fries":
            has_fries = True
        if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
            has_drink = True
        if it["name"] == "Chicken Wrap":
            has_wrap = True
        if it["name"] == "Salad":
            has_salad = True
        if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
            has_drink2 = True

    if has_burger and has_fries and has_drink:
        # find the burger, fries, drink items and apply 15% combo discount
        for it in items_result:
            if it["name"] == "Burger" or it["name"] == "Cheeseburger" or it["name"] == "Veggie Burger":
                d = round(it["unit_price"] * 1 * 0.15, 2)
                combo_discount = combo_discount + d
                break
        for it in items_result:
            if it["name"] == "Fries" or it["name"] == "Large Fries":
                d = round(it["unit_price"] * 1 * 0.15, 2)
                combo_discount = combo_discount + d
                break
        for it in items_result:
            if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
                d = round(it["unit_price"] * 1 * 0.15, 2)
                combo_discount = combo_discount + d
                break

    if has_wrap and has_salad and has_drink2:
        # find the wrap, salad, drink items and apply 10% combo discount
        # but only if combo 1 didn't already use the drink
        drink_used_by_combo1 = has_burger and has_fries and has_drink
        for it in items_result:
            if it["name"] == "Chicken Wrap":
                d = round(it["unit_price"] * 1 * 0.10, 2)
                combo_discount = combo_discount + d
                break
        for it in items_result:
            if it["name"] == "Salad":
                d = round(it["unit_price"] * 1 * 0.10, 2)
                combo_discount = combo_discount + d
                break
        # check if we have a second drink for this combo
        drink_count = 0
        for it in items_result:
            if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
                drink_count = drink_count + it["quantity"]
        if drink_used_by_combo1:
            if drink_count >= 2:
                for it in items_result:
                    if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
                        d = round(it["unit_price"] * 1 * 0.10, 2)
                        combo_discount = combo_discount + d
                        break
            else:
                # not enough drinks for second combo, remove the wrap+salad discount
                combo_discount = combo_discount - round(items_result[[x["name"] for x in items_result].index("Chicken Wrap")]["unit_price"] * 0.10, 2)
                combo_discount = combo_discount - round(items_result[[x["name"] for x in items_result].index("Salad")]["unit_price"] * 0.10, 2)
        else:
            for it in items_result:
                if it["name"] == "Soda" or it["name"] == "Large Soda" or it["name"] == "Water" or it["name"] == "Lemonade":
                    d = round(it["unit_price"] * 1 * 0.10, 2)
                    combo_discount = combo_discount + d
                    break

    combo_discount = round(combo_discount, 2)

    # coupon code discounts
    coupon_discount = 0.0
    if "coupon_code" in order_data:
        if order_data["coupon_code"] is not None:
            if isinstance(order_data["coupon_code"], str):
                cc = order_data["coupon_code"].strip().upper()
                if cc == "SAVE10":
                    # 10% off subtotal
                    coupon_discount = round(st * 0.10, 2)
                elif cc == "SAVE5":
                    # $5 off if subtotal >= $20
                    if st >= 20.0:
                        coupon_discount = 5.0
                    else:
                        coupon_discount = 0.0
                elif cc == "FREEWATER":
                    # remove cost of water items
                    for it in items_result:
                        if it["name"] == "Water":
                            coupon_discount = coupon_discount + it["total_price"]
                elif cc == "BOGO50":
                    # 50% off cheapest item
                    cheapest = None
                    for it in items_result:
                        if cheapest is None:
                            cheapest = it["unit_price"]
                        else:
                            if it["unit_price"] < cheapest:
                                cheapest = it["unit_price"]
                    if cheapest is not None:
                        coupon_discount = round(cheapest * 0.50, 2)
                elif cc == "":
                    coupon_discount = 0.0
                else:
                    raise ValueError("Invalid coupon code: " + order_data["coupon_code"])
            else:
                raise ValueError("Coupon code must be a string")

    coupon_discount = round(coupon_discount, 2)

    # total discount so far
    total_discount = round(combo_discount + coupon_discount, 2)

    # apply discount to subtotal
    after_discount = round(st - total_discount, 2)
    if after_discount < 0:
        after_discount = 0.0

    # tax calculation based on state
    tax = 0.0
    if "state" in order_data:
        if order_data["state"] is not None:
            s = order_data["state"].upper().strip()
            if s == "CA":
                tax = round(after_discount * 0.0725, 2)
            elif s == "TX":
                tax = round(after_discount * 0.0625, 2)
            elif s == "NY":
                tax = round(after_discount * 0.08, 2)
            elif s == "FL":
                tax = round(after_discount * 0.06, 2)
            elif s == "WA":
                tax = round(after_discount * 0.065, 2)
            elif s == "OR":
                tax = 0.0
            elif s == "NV":
                tax = round(after_discount * 0.0685, 2)
            elif s == "AZ":
                tax = round(after_discount * 0.056, 2)
            elif s == "CO":
                tax = round(after_discount * 0.029, 2)
            elif s == "IL":
                tax = round(after_discount * 0.0625, 2)
            elif s == "PA":
                tax = round(after_discount * 0.06, 2)
            elif s == "OH":
                tax = round(after_discount * 0.0575, 2)
            elif s == "GA":
                tax = round(after_discount * 0.04, 2)
            elif s == "NC":
                tax = round(after_discount * 0.0475, 2)
            elif s == "MI":
                tax = round(after_discount * 0.06, 2)
            else:
                # default tax rate
                tax = round(after_discount * 0.05, 2)
        else:
            tax = round(after_discount * 0.05, 2)
    else:
        tax = round(after_discount * 0.05, 2)

    # loyalty points discount
    loyalty_discount = 0.0
    loyalty_points_used = 0
    if "loyalty_points" in order_data:
        if order_data["loyalty_points"] is not None:
            if isinstance(order_data["loyalty_points"], int):
                if order_data["loyalty_points"] > 0:
                    lp = order_data["loyalty_points"]
                    # each 10 points = $1 discount, max 50% of after_discount
                    max_loyalty_discount = round(after_discount * 0.50, 2)
                    potential_discount = round((lp // 10) * 1.0, 2)
                    if potential_discount > max_loyalty_discount:
                        loyalty_discount = max_loyalty_discount
                        loyalty_points_used = int(max_loyalty_discount * 10)
                    else:
                        loyalty_discount = potential_discount
                        loyalty_points_used = (lp // 10) * 10
                elif order_data["loyalty_points"] < 0:
                    raise ValueError("Loyalty points cannot be negative")
                else:
                    loyalty_discount = 0.0
                    loyalty_points_used = 0
            else:
                raise ValueError("Loyalty points must be an integer")
    loyalty_discount = round(loyalty_discount, 2)

    # calculate total
    total = round(after_discount + tax - loyalty_discount, 2)
    if total < 0:
        total = 0.0

    # loyalty points earned (1 point per dollar spent, rounded down)
    points_earned = int(total)

    # generate order id
    oid = "ORD-" + str(uuid.uuid4())[:8].upper()

    # build summary - tried different approaches, this one works
    # attempt 1: f-string (commented out)
    # summary = f"Order for {cid}: {tq} items, ${total:.2f}"
    # attempt 2: format method (commented out)
    # summary = "Order for {}: {} items, ${:.2f}".format(cid, tq, total)
    # attempt 3: string concatenation (using this one)
    summary = "Order for " + cid + ": " + str(tq) + " items, $" + "{:.2f}".format(total)

    # validate the total one more time just to be safe
    if not isinstance(total, float):
        try:
            total = float(total)
        except:
            total = 0.0
    if total < 0:
        total = 0.0
    if total > 99999.99:
        total = 99999.99

    # validate points earned
    if points_earned < 0:
        points_earned = 0
    if points_earned > 9999:
        points_earned = 9999

    # make sure all the numbers are properly rounded
    st = round(st, 2)
    combo_discount = round(combo_discount, 2)
    coupon_discount = round(coupon_discount, 2)
    total_discount = round(total_discount, 2)
    tax = round(tax, 2)
    loyalty_discount = round(loyalty_discount, 2)
    total = round(total, 2)

    # build result
    r["order_id"] = oid
    r["customer_id"] = cid
    r["items"] = items_result
    r["subtotal"] = round(st, 2)
    r["combo_discount"] = combo_discount
    r["coupon_discount"] = coupon_discount
    r["discount"] = total_discount
    r["tax"] = tax
    r["loyalty_discount"] = loyalty_discount
    r["loyalty_points_used"] = loyalty_points_used
    r["total"] = total
    r["loyalty_points_earned"] = points_earned
    r["summary"] = summary
    r["timestamp"] = datetime.datetime.now().isoformat()
    r["state"] = order_data.get("state", None)
    r["coupon_code"] = order_data.get("coupon_code", None)

    return r
