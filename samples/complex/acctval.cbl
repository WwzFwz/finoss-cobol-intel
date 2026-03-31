       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTVAL.
      *
      * Account validation program.
      * Heavy business logic with nested IF and EVALUATE.
      *
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ACCOUNT.
           05  WS-ACCT-NUM         PIC X(12).
           05  WS-ACCT-TYPE        PIC X(2).
           88  ACCT-SAVINGS        VALUE "SA".
           88  ACCT-CHECKING       VALUE "CA".
           88  ACCT-LOAN           VALUE "LN".
           88  ACCT-DEPOSIT        VALUE "TD".
           05  WS-ACCT-STATUS      PIC X(1).
           88  ACCT-ACTIVE         VALUE "A".
           88  ACCT-DORMANT        VALUE "D".
           88  ACCT-CLOSED         VALUE "C".
           88  ACCT-FROZEN         VALUE "F".
       01  WS-VALIDATION-RESULT.
           05  WS-VALID            PIC X(1).
           05  WS-REASON           PIC X(40).
       01  WS-ACCT-LENGTH          PIC 9(2).
       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM VALIDATE-ACCOUNT
           DISPLAY WS-VALID
           DISPLAY WS-REASON
           STOP RUN.
       VALIDATE-ACCOUNT.
           MOVE "Y" TO WS-VALID
           MOVE SPACES TO WS-REASON
           IF WS-ACCT-NUM = SPACES
               MOVE "N" TO WS-VALID
               MOVE "ACCOUNT NUMBER IS EMPTY" TO WS-REASON
           ELSE
               IF ACCT-CLOSED
                   MOVE "N" TO WS-VALID
                   MOVE "ACCOUNT IS CLOSED" TO WS-REASON
               ELSE
                   IF ACCT-FROZEN
                       MOVE "N" TO WS-VALID
                       MOVE "ACCOUNT IS FROZEN" TO WS-REASON
                   ELSE
                       PERFORM CHECK-ACCOUNT-TYPE
                   END-IF
               END-IF
           END-IF.
       CHECK-ACCOUNT-TYPE.
           EVALUATE TRUE
               WHEN ACCT-SAVINGS
                   MOVE "SAVINGS ACCOUNT VALID" TO WS-REASON
               WHEN ACCT-CHECKING
                   MOVE "CHECKING ACCOUNT VALID" TO WS-REASON
               WHEN ACCT-LOAN
                   MOVE "LOAN ACCOUNT VALID" TO WS-REASON
               WHEN ACCT-DEPOSIT
                   MOVE "TIME DEPOSIT VALID" TO WS-REASON
               WHEN OTHER
                   MOVE "N" TO WS-VALID
                   MOVE "UNKNOWN ACCOUNT TYPE" TO WS-REASON
           END-EVALUATE.
