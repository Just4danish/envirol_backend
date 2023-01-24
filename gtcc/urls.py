from django.urls import path
from .views import *

urlpatterns = [
    path('gtcc', GTCCList.as_view()),
    path('gtcc/<int:pk>', GTCCDetails.as_view()),
    path('gtcc_dropdownlist', GTCCDropdownList.as_view()),
    path('gtcc_and_drivers', GTCCAndDriversList.as_view()),
    path('payment_detail',PaymentList.as_view()),
    path('payment_detail/<int:pk>',PaymentDetails.as_view()),
    path('vehicle_detail',VehicleList.as_view()),
    path('vehicle_detail/<int:pk>',VehicleDetails.as_view()),
    path('driver',DriverList.as_view()),
    path('driver/<int:pk>',DriverDetails.as_view()),
    path('vehicle_qrcode_scan', VehicleQRCodeScan.as_view()),
    path('unlink_vehicle_from_driver', UnlinkVehicleFromDriver.as_view()),
    path('vehicle_qrcode_scan_for_operator', VehicleQRCodeScanForOperator.as_view()),
    path('vehicle_qrcode_check', VehicleQRCodeCheck.as_view()),
    path('assign_vehicle_for_service_request', AssignVehicleToServiceRequest.as_view()),
    path('driver_service_request_count', DriverServiceRequestCount.as_view()),
    path('driver_service_request_details', DriverServiceRequestDetails.as_view()),
    path('operator_service_request_details/<int:vehicle_entry_details_id>', OperatorServiceRequestDetails.as_view()),
    path('gtcc_service_request_detail', GTCCServiceRequestDetails.as_view()),
    path('service_request_grease_traps/<int:service_request_id>', ServiceRequestGreaseTraps.as_view()),
    path('service_request_grease_traps_for_mobile/<int:service_request_id>', ServiceRequestGreaseTrapsForMobileApp.as_view()),
    path('gtcc_vehiclelist/<int:gtcc_id>', GTCCVehicleList.as_view()),
    path('update_service_request', UpdateServiceRequest.as_view()),
    # path('update_service_request_details', UpdateServiceRequestDetails.as_view()),
    path('update_service_request_grease_trap_details', UpdateServiceRequestGreaseTrapDetails.as_view()),
    path('booklet', BookletList.as_view()),
    path('booklet/<int:active>', BookletList.as_view()),
    path('booklet_detail/<int:pk>',BookletDetails.as_view()),
    path('coupon_booklet', CouponBookletList.as_view()),
    path('coupon_booklet_detail/<int:pk>',CouponBookletDetails.as_view()),
    path('coupon', CouponList.as_view()),
    path('adddeletecoupon/<int:pk>', AddDeleteCouponView.as_view()),
    # path('accesscontrol/access_entry', AccessEntryView.as_view()),
    path('vehiclelist_operator', VehicleListForOperatorView.as_view()),
    path('vehicle_details_operator/<int:pk>', VehicleDetailsForOperatorView.as_view()),
    path('rfid_detection_for_vehicle', RFIDDetectionForVehicle.as_view()),
    path('rfid_detection_for_vehicle_test/<str:rfid>', RFIDDetectionForVehicleTemp.as_view()),
    path('gtcc_contract_list', GTCCContractList.as_view()),
    path('approve_or_reject_entity_contract', ApproveOrRejectEntityContract.as_view()),
    path('vehicle_status_update', VehicleStatusUpdate.as_view()),#this is temporary, needs to remove.
    path('operator_dumping_acceptance_view', OperatorDumpingAcceptanceView.as_view()),
    path('gtcc_coupon_booklet', GTCCCouponBooklet.as_view()),
    path('gtcc_used_coupon_list', GTCCUsedCouponList.as_view()),
    path('discharge_txn_report', DischargeTxnReport.as_view()),
    path('coupon_report', CouponReport.as_view()),
    path('edit_coupon_gallons/<int:pk>',EditCouponGallons.as_view()),
    path('edit_coupon_log_list', EditCouponLogList.as_view()),
    path('jobs_and_coupon_based_on_vehicle_entry_details/<int:vehicle_entry_id>',JobsAndCouponListBasedOnVehicleEntryDetails.as_view()),
]

#Dashboard API URLS
urlpatterns += [
    path('wallet_details', WalletDetails.as_view()),
    path('transaction_details', TransactionDetails.as_view()),
    path('dumping_details', DumpingDetails.as_view()),
    path('vehicle_status', VehicleStatus.as_view()),
]