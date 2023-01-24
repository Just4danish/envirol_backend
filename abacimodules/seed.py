from masters.models import ModeOfPayment
mode_of_payments = [
    {
        "id" : 1,
        "mop_id" : 1001,
        "mode_of_payment" : "Online Payment",
        "is_editable" : False,
        "created_by_id" : 1
    },
    {
        "id" : 2,
        "mop_id" : 1002,
        "mode_of_payment" : "DO Adjustment",
        "is_editable" : False,
        "created_by_id" : 1
    },
    {
        "id" : 3,
        "mop_id" : 1003,
        "mode_of_payment" : "Credit Refund",
        "is_editable" : False,
        "created_by_id" : 1
    },
]
ModeOfPayment.objects.bulk_create(mode_of_payments)