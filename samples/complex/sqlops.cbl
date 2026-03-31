       IDENTIFICATION DIVISION.
       PROGRAM-ID. SQLOPS.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-RAW-NAME               PIC X(30) VALUE "DOE,JOHN".
       01 WS-LAST-NAME              PIC X(15).
       01 WS-FIRST-NAME             PIC X(15).
       01 WS-COMMA-COUNT            PIC 9(2) VALUE 0.
       01 WS-ID                     PIC 9(10).
       01 WS-NAME                   PIC X(30).

       LINKAGE SECTION.
       01 LK-REQUEST.
           05 LK-CUST-ID            PIC 9(10).

       PROCEDURE DIVISION USING LK-REQUEST.
       MAIN-PROGRAM.
           UNSTRING WS-RAW-NAME
               DELIMITED BY ","
               INTO WS-LAST-NAME WS-FIRST-NAME.
           INSPECT WS-RAW-NAME
               TALLYING WS-COMMA-COUNT
               FOR ALL ",".
           INSPECT WS-NAME
               REPLACING ALL "-" BY " ".
           EXEC SQL
               SELECT CUST_NAME
               INTO :WS-NAME
               FROM CUSTOMER_TABLE
               WHERE CUST_ID = :LK-CUST-ID
           END-EXEC.
           GOBACK.
