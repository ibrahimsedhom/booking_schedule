# Booking Schedule - Frappe App Migration

I have successfully converted the Node.js "Booking Schedule" application into a Frappe App structure. This app contains all the original data models and business logic, ready to be installed on a Frappe site.

## 📂 App Structure
The app is located in `apps/booking_schedule` and follows the standard Frappe layout:

```
apps/booking_schedule/
├── booking_schedule/
│   ├── doctype/
│   │   ├── bs_merchant/             # Merchant Data Model
│   │   ├── bs_booking/              # Booking Data Model
│   │   ├── bs_public_holiday/       # Holiday Data Model
│   │   └── bs_delivery_schedule_item/ # Child Table for Schedule
│   ├── api.py                       # Core Business Logic (Controllers)
│   └── hooks.py                     # App Configuration
├── setup.py
└── requirements.txt
```

## 📊 Data Models (DocTypes)

### 1. BS Merchant
- Stores merchant details and delivery configurations.
- **Key Fields**: `ns_merchant_id`, `delivery_schedule` (Table)

### 2. BS Booking
- Stores individual delivery appointments.
- **Key Fields**: `date`, `time_from`, `time_to`, `merchant_ns_id`

### 3. BS Public Holiday
- Stores dates to be excluded from scheduling.

## 🚀 API & Business Logic
The core logic has been ported to `apps/booking_schedule/booking_schedule/api.py`.

### Available Whitelisted Methods:

1.  **get_delivery_schedule(merchant_ns_id)**
    - **Logic**: Calculates available slots based on capacity, holidays, and existing bookings.
    - **Usage**: POST to `/api/method/booking_schedule.booking_schedule.api.get_delivery_schedule`

2.  **create_booking(date, time_from, time_to, merchant_ns_id)**
    - **Logic**: Validates merchant and creates a new booking.
    - **Usage**: POST to `/api/method/booking_schedule.booking_schedule.api.create_booking`

3.  **search_bookings(merchant_ns_id, date, time_from, time_to)**
    - **Logic**: Search bookings by date/time range.
    - **Usage**: POST to `/api/method/booking_schedule.booking_schedule.api.search_bookings`

4.  **update_booking(booking_id, data)**
    - **Usage**: POST to `/api/method/booking_schedule.booking_schedule.api.update_booking`

5.  **delete_booking(booking_id)**
    - **Usage**: POST to `/api/method/booking_schedule.booking_schedule.api.delete_booking`

## 🛠️ How to Install
1.  Initialize a git repository in `apps/booking_schedule`.
2.  Push to a remote server.
3.  On your Frappe server, run:
    ```bash
    bench get-app [your-repo-url]
    bench install-app booking_schedule
    ```
