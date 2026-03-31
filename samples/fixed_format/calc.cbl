       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALC.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-NUM1            PIC 9(3) VALUE 0.
       01 WS-NUM2            PIC 9(3) VALUE 0.
       01 WS-RESULT          PIC 9(5) VALUE 0.
       01 WS-OPERATION       PIC X VALUE SPACE.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           MOVE 100 TO WS-NUM1.
           MOVE 50 TO WS-NUM2.
           MOVE "A" TO WS-OPERATION.
           PERFORM CALCULATE.
           DISPLAY "RESULT: " WS-RESULT.
           STOP RUN.

       VALIDATE-INPUT.
           IF WS-NUM1 = 0
               DISPLAY "NUM1 IS ZERO"
           ELSE
               DISPLAY "NUM1 IS NOT ZERO"
           END-IF.

       CALCULATE.
           EVALUATE WS-OPERATION
               WHEN "A"
                   ADD WS-NUM1 TO WS-NUM2
                       GIVING WS-RESULT
               WHEN "S"
                   SUBTRACT WS-NUM2 FROM WS-NUM1
                       GIVING WS-RESULT
               WHEN "M"
                   MULTIPLY WS-NUM1 BY WS-NUM2
                       GIVING WS-RESULT
               WHEN OTHER
                   DISPLAY "UNKNOWN OPERATION"
           END-EVALUATE.
