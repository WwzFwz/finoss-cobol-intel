       IDENTIFICATION DIVISION.
       PROGRAM-ID. FILEBATCH.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-FILE ASSIGN TO "INPUT.DAT".
           SELECT OUT-FILE ASSIGN TO "OUTPUT.DAT".

       DATA DIVISION.
       FILE SECTION.
       FD IN-FILE.
       01 IN-REC.
           05 IN-ACCOUNT            PIC X(10).
           05 IN-AMOUNT             PIC 9(7)V99.

       FD OUT-FILE.
       01 OUT-REC.
           05 OUT-ACCOUNT           PIC X(10).
           05 OUT-AMOUNT            PIC 9(7)V99.

       WORKING-STORAGE SECTION.
       01 WS-EOF                   PIC X VALUE "N".

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           OPEN INPUT IN-FILE OUTPUT OUT-FILE.
           READ IN-FILE AT END
               MOVE "Y" TO WS-EOF.
           WRITE OUT-REC FROM IN-REC.
           REWRITE OUT-REC FROM IN-REC.
           CLOSE IN-FILE OUT-FILE.
           STOP RUN.
