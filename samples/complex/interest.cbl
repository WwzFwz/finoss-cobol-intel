       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALCINT.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-ACCOUNT-DATA.
           05 WS-ACCOUNT-NUMBER    PIC 9(10).
           05 WS-ACCOUNT-TYPE      PIC X.
               88 ACCT-SAVINGS     VALUE "S".
               88 ACCT-CHECKING    VALUE "C".
               88 ACCT-FIXED       VALUE "F".
           05 WS-BALANCE           PIC 9(9)V99 COMP-3.
           05 WS-TENURE-YEARS      PIC 9(2) COMP.

       01 WS-DATE-NUM              PIC 9(8).
       01 WS-DATE-STR REDEFINES WS-DATE-NUM.
           05 WS-YEAR              PIC 9(4).
           05 WS-MONTH             PIC 9(2).
           05 WS-DAY               PIC 9(2).

       01 WS-MONTHLY-DATA.
           05 WS-MONTH-ENTRY OCCURS 12 TIMES.
               10 WS-MONTH-AMOUNT  PIC 9(9)V99 COMP-3.
               10 WS-MONTH-RATE    PIC 9V9(4).

       01 WS-RATE                  PIC 9V9(4) VALUE 0.
       01 WS-INTEREST              PIC 9(9)V99 VALUE 0.
       01 WS-IDX                   PIC 9(2) VALUE 0.
       01 WS-RESULT                PIC 9(9)V99 VALUE 0.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM DETERMINE-RATE.
           PERFORM CALCULATE-INTEREST.
           CALL "LOGTRX" USING WS-ACCOUNT-DATA WS-INTEREST.
           DISPLAY "INTEREST: " WS-INTEREST.
           STOP RUN.

       DETERMINE-RATE.
           EVALUATE TRUE
               WHEN ACCT-SAVINGS
                   IF WS-BALANCE > 10000
                       AND WS-TENURE-YEARS >= 2
                       MOVE 0.0500 TO WS-RATE
                   ELSE
                       MOVE 0.0250 TO WS-RATE
                   END-IF
               WHEN ACCT-CHECKING
                   MOVE 0.0100 TO WS-RATE
               WHEN ACCT-FIXED
                   IF WS-TENURE-YEARS >= 5
                       MOVE 0.0750 TO WS-RATE
                   ELSE
                       MOVE 0.0600 TO WS-RATE
                   END-IF
               WHEN OTHER
                   MOVE 0 TO WS-RATE
           END-EVALUATE.

       CALCULATE-INTEREST.
           COMPUTE WS-INTEREST = WS-BALANCE * WS-RATE.
           PERFORM VARYING WS-IDX FROM 1 BY 1
               UNTIL WS-IDX > 12
               COMPUTE WS-MONTH-AMOUNT(WS-IDX) =
                   WS-BALANCE * WS-RATE / 12
               MOVE WS-RATE TO WS-MONTH-RATE(WS-IDX)
           END-PERFORM.
