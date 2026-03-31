       01 CUSTOMER-RECORD.
           05 CUST-ID          PIC 9(8).
           05 CUST-NAME        PIC X(30).
           05 CUST-TYPE        PIC X.
               88 CUST-INDIVIDUAL VALUE "I".
               88 CUST-CORPORATE  VALUE "C".
           05 CUST-BALANCE     PIC 9(9)V99.
           05 CUST-STATUS      PIC X.
               88 CUST-ACTIVE     VALUE "A".
               88 CUST-INACTIVE   VALUE "I".
