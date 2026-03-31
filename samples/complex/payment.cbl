       IDENTIFICATION DIVISION.
       PROGRAM-ID. PAYMENT.
      *
      * Payment processing program.
      * Calls DATEUTIL for date validation and BALCHK for
      * balance verification before processing payment.
      *
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PAYMENT-DATA.
           05  WS-ACCOUNT-FROM     PIC X(10).
           05  WS-ACCOUNT-TO       PIC X(10).
           05  WS-AMOUNT           PIC 9(9)V99 COMP-3.
           05  WS-CURRENCY         PIC X(3).
           88  CURRENCY-IDR        VALUE "IDR".
           88  CURRENCY-USD        VALUE "USD".
           88  CURRENCY-SGD        VALUE "SGD".
           05  WS-PAYMENT-TYPE     PIC X(1).
           88  PAY-TRANSFER        VALUE "T".
           88  PAY-BILL            VALUE "B".
           88  PAY-TOPUP           VALUE "U".
       01  WS-RESULT.
           05  WS-STATUS           PIC X(2).
           88  STATUS-OK           VALUE "00".
           88  STATUS-INSUF-BAL    VALUE "51".
           88  STATUS-INVALID-ACCT VALUE "14".
           88  STATUS-INVALID-DATE VALUE "13".
           05  WS-MESSAGE          PIC X(50).
       01  WS-DATE-VALID           PIC X(1).
       01  WS-BALANCE-OK           PIC X(1).
       01  WS-FEE                  PIC 9(5)V99 COMP-3.
       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM VALIDATE-PAYMENT
           IF STATUS-OK
               PERFORM CALCULATE-FEE
               PERFORM PROCESS-PAYMENT
           END-IF
           DISPLAY WS-STATUS
           DISPLAY WS-MESSAGE
           STOP RUN.
       VALIDATE-PAYMENT.
           CALL "DATEUTIL" USING WS-DATE-VALID
           IF WS-DATE-VALID = "N"
               MOVE "13" TO WS-STATUS
               MOVE "INVALID TRANSACTION DATE" TO WS-MESSAGE
           ELSE
               CALL "BALCHK" USING WS-ACCOUNT-FROM WS-AMOUNT
                   WS-BALANCE-OK
               IF WS-BALANCE-OK = "N"
                   MOVE "51" TO WS-STATUS
                   MOVE "INSUFFICIENT BALANCE" TO WS-MESSAGE
               ELSE
                   MOVE "00" TO WS-STATUS
               END-IF
           END-IF.
       CALCULATE-FEE.
           EVALUATE TRUE
               WHEN PAY-TRANSFER
                   IF CURRENCY-IDR
                       COMPUTE WS-FEE = WS-AMOUNT * 0.001
                   ELSE
                       COMPUTE WS-FEE = WS-AMOUNT * 0.005
                   END-IF
               WHEN PAY-BILL
                   MOVE 2500 TO WS-FEE
               WHEN PAY-TOPUP
                   MOVE 0 TO WS-FEE
               WHEN OTHER
                   MOVE 5000 TO WS-FEE
           END-EVALUATE.
       PROCESS-PAYMENT.
           SUBTRACT WS-AMOUNT FROM WS-AMOUNT
           SUBTRACT WS-FEE FROM WS-AMOUNT
           MOVE "PAYMENT PROCESSED" TO WS-MESSAGE.
