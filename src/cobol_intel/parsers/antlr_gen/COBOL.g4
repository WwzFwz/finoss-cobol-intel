// COBOL 85 Subset Grammar — cobol-intel ANTLR4 PoC
// Same subset as lark grammar for fair comparison.
// Assumes preprocessed input: uppercase, fixed-format stripped, PIC strings quoted.

grammar COBOL;

// =================== Parser Rules ===================

program
    : identificationDivision environmentDivision? dataDivision? procedureDivision? EOF
    ;

identificationDivision
    : IDENTIFICATION DIVISION DOT PROGRAM_ID DOT NAME DOT
    ;

// --- ENVIRONMENT DIVISION ---

environmentDivision
    : ENVIRONMENT DIVISION DOT inputOutputSection?
    ;

inputOutputSection
    : INPUT_OUTPUT SECTION DOT fileControlParagraph?
    ;

fileControlParagraph
    : FILE_CONTROL DOT selectEntry*
    ;

selectEntry
    : SELECT NAME ASSIGN TO (NAME | STRING_LIT) DOT
    ;

// --- DATA DIVISION ---

dataDivision
    : DATA DIVISION DOT dataSection*
    ;

dataSection
    : WORKING_STORAGE SECTION DOT dataEntry*
    | FILE SECTION DOT fileEntry*
    | LINKAGE SECTION DOT dataEntry*
    ;

fileEntry
    : fileDescription
    | dataEntry
    ;

fileDescription
    : (FD | SD) NAME DOT
    ;

dataEntry
    : copyEntry
    | conditionEntry
    | dataItem
    ;

copyEntry
    : COPY NAME replacingClause? DOT
    ;

replacingClause
    : REPLACING replacePair+
    ;

replacePair
    : copyReplaceToken BY copyReplaceToken
    ;

copyReplaceToken
    : PSEUDO_TEXT
    | STRING_LIT
    | NAME
    | NUMBER
    ;

conditionEntry
    : LEVEL_88 NAME VALUE literal DOT
    ;

dataItem
    : NUMBER NAME dataClause* DOT
    ;

dataClause
    : picClause
    | usageClause
    | valueClause
    | occursClause
    | redefinesClause
    ;

picClause       : (PIC | PICTURE) STRING_LIT ;
usageClause     : COMP_3 | COMP_5 | COMP | BINARY | PACKED_DECIMAL | DISPLAY ;
valueClause     : VALUE literal ;
occursClause    : OCCURS NUMBER TIMES? ;
redefinesClause : REDEFINES NAME ;

// --- PROCEDURE DIVISION ---

procedureDivision
    : PROCEDURE DIVISION procedureUsing? DOT paragraph*
    ;

procedureUsing
    : USING nameRef+
    ;

paragraph
    : NAME DOT sentence*
    ;

sentence
    : statement+ DOT
    ;

statement
    : displayStmt
    | moveStmt
    | computeStmt
    | addStmt
    | subtractStmt
    | multiplyStmt
    | performInlineStmt
    | performSimpleStmt
    | callStmt
    | openStmt
    | closeStmt
    | readStmt
    | writeStmt
    | rewriteStmt
    | execSqlStmt
    | ifStmt
    | evaluateStmt
    | stringStmt
    | unstringStmt
    | inspectStmt
    | stopStmt
    | gobackStmt
    ;

displayStmt         : DISPLAY operand+ ;
moveStmt            : MOVE operand TO nameRef+ ;
computeStmt         : COMPUTE nameRef EQ expression ;
addStmt             : ADD operand TO operand (GIVING nameRef)? ;
subtractStmt        : SUBTRACT operand FROM operand (GIVING nameRef)? ;
multiplyStmt        : MULTIPLY operand BY operand (GIVING nameRef)? ;
performInlineStmt   : PERFORM VARYING NAME FROM operand BY operand UNTIL condition statement* END_PERFORM ;
performSimpleStmt   : PERFORM NAME ;
callStmt            : CALL STRING_LIT USING nameRef+ ;
openStmt            : OPEN openPhrase+ ;
openPhrase          : openMode nameRef+ ;
openMode            : INPUT | OUTPUT | I_O | EXTEND ;
closeStmt           : CLOSE nameRef+ ;
readStmt            : READ nameRef (INTO nameRef)? atEndClause? ;
atEndClause         : AT END statement* ;
writeStmt           : WRITE nameRef (FROM operand)? ;
rewriteStmt         : REWRITE nameRef (FROM operand)? ;
execSqlStmt         : EXEC SQL sqlAtom+ END_EXEC ;
ifStmt              : IF condition statement* elseClause? END_IF ;
elseClause          : ELSE statement* ;
evaluateStmt        : EVALUATE evalSubject whenClause+ END_EVALUATE ;
evalSubject         : TRUE_KW | operand ;
whenClause          : WHEN OTHER statement*
                    | WHEN whenMatch statement*
                    ;
whenMatch           : NAME | literal ;
stringStmt          : STRING_KW operand+ DELIMITED BY delimTarget INTO nameRef ;
unstringStmt        : UNSTRING operand DELIMITED BY delimTarget INTO nameRef+ ;
inspectStmt         : INSPECT nameRef inspectClause ;
inspectClause       : inspectTallyingClause
                    | inspectReplacingClause
                    ;
inspectTallyingClause : TALLYING nameRef FOR ALL literal ;
inspectReplacingClause: REPLACING ALL literal BY literal ;
delimTarget         : SIZE | operand ;
stopStmt            : STOP RUN ;
gobackStmt          : GOBACK ;

// --- CONDITIONS ---

condition
    : simpleCondition ((AND | OR) simpleCondition)*
    ;

simpleCondition
    : operand compOp operand
    | NOT simpleCondition
    | NAME
    ;

compOp : GT | LT | GTE | LTE | EQ | NOT EQ ;

// --- EXPRESSIONS ---

expression : term ((PLUS | MINUS) term)* ;
term       : factor ((STAR | SLASH) factor)* ;
factor     : operand | LPAREN expression RPAREN ;

// --- OPERANDS ---

operand : nameRef | literal ;

nameRef
    : NAME LPAREN expression RPAREN
    | NAME
    ;

literal
    : STRING_LIT
    | DECIMAL
    | NUMBER
    | figConst
    ;

figConst
    : SPACE_KW | SPACES | ZERO | ZEROS | ZEROES
    | HIGH_VALUE | HIGH_VALUES | LOW_VALUE | LOW_VALUES
    ;

sqlAtom
    : NAME
    | SQL_IDENT
    | SELECT
    | INTO
    | FROM
    | NUMBER
    | DECIMAL
    | STRING_LIT
    | STAR
    | EQ
    | GT
    | LT
    | GTE
    | LTE
    | LPAREN
    | RPAREN
    | COMMA
    | COLON
    ;

// =================== Lexer Rules ===================
// Order matters: keywords MUST come before NAME.

// Division / section keywords
IDENTIFICATION  : 'IDENTIFICATION' ;
DIVISION        : 'DIVISION' ;
PROGRAM_ID      : 'PROGRAM-ID' ;
ENVIRONMENT     : 'ENVIRONMENT' ;
DATA            : 'DATA' ;
INPUT_OUTPUT    : 'INPUT-OUTPUT' ;
FILE_CONTROL    : 'FILE-CONTROL' ;
WORKING_STORAGE : 'WORKING-STORAGE' ;
SECTION         : 'SECTION' ;
FILE            : 'FILE' ;
LINKAGE         : 'LINKAGE' ;
PROCEDURE       : 'PROCEDURE' ;

// Data keywords
COPY            : 'COPY' ;
SELECT          : 'SELECT' ;
ASSIGN          : 'ASSIGN' ;
REPLACING       : 'REPLACING' ;
PIC             : 'PIC' ;
PICTURE         : 'PICTURE' ;
VALUE           : 'VALUE' ;
OCCURS          : 'OCCURS' ;
TIMES           : 'TIMES' ;
REDEFINES       : 'REDEFINES' ;
FD              : 'FD' ;
SD              : 'SD' ;
COMP_3          : 'COMP-3' ;
COMP_5          : 'COMP-5' ;
COMP            : 'COMP' ;
BINARY          : 'BINARY' ;
PACKED_DECIMAL  : 'PACKED-DECIMAL' ;

// Statement keywords
DISPLAY         : 'DISPLAY' ;
MOVE            : 'MOVE' ;
TO              : 'TO' ;
COMPUTE         : 'COMPUTE' ;
ADD             : 'ADD' ;
SUBTRACT        : 'SUBTRACT' ;
FROM            : 'FROM' ;
MULTIPLY        : 'MULTIPLY' ;
GIVING          : 'GIVING' ;
PERFORM         : 'PERFORM' ;
VARYING         : 'VARYING' ;
BY              : 'BY' ;
UNTIL           : 'UNTIL' ;
END_PERFORM     : 'END-PERFORM' ;
CALL            : 'CALL' ;
USING           : 'USING' ;
OPEN            : 'OPEN' ;
INPUT           : 'INPUT' ;
OUTPUT          : 'OUTPUT' ;
I_O             : 'I-O' ;
EXTEND          : 'EXTEND' ;
CLOSE           : 'CLOSE' ;
READ            : 'READ' ;
WRITE           : 'WRITE' ;
REWRITE         : 'REWRITE' ;
AT              : 'AT' ;
END             : 'END' ;
EXEC            : 'EXEC' ;
SQL             : 'SQL' ;
END_EXEC        : 'END-EXEC' ;
IF              : 'IF' ;
ELSE            : 'ELSE' ;
END_IF          : 'END-IF' ;
EVALUATE        : 'EVALUATE' ;
WHEN            : 'WHEN' ;
OTHER           : 'OTHER' ;
END_EVALUATE    : 'END-EVALUATE' ;
TRUE_KW         : 'TRUE' ;
STRING_KW       : 'STRING' ;
UNSTRING        : 'UNSTRING' ;
INSPECT         : 'INSPECT' ;
TALLYING        : 'TALLYING' ;
FOR             : 'FOR' ;
ALL             : 'ALL' ;
DELIMITED       : 'DELIMITED' ;
SIZE            : 'SIZE' ;
INTO            : 'INTO' ;
STOP            : 'STOP' ;
RUN             : 'RUN' ;
GOBACK          : 'GOBACK' ;

// Logic keywords
AND             : 'AND' ;
OR              : 'OR' ;
NOT             : 'NOT' ;

// Figurative constants
SPACE_KW        : 'SPACE' ;
SPACES          : 'SPACES' ;
ZERO            : 'ZERO' ;
ZEROS           : 'ZEROS' ;
ZEROES          : 'ZEROES' ;
HIGH_VALUE      : 'HIGH-VALUE' ;
HIGH_VALUES     : 'HIGH-VALUES' ;
LOW_VALUE       : 'LOW-VALUE' ;
LOW_VALUES      : 'LOW-VALUES' ;

// Level 88
LEVEL_88        : '88' ;

// Operators
GTE             : '>=' ;
LTE             : '<=' ;
GT              : '>' ;
LT              : '<' ;
EQ              : '=' ;
PLUS            : '+' ;
MINUS           : '-' ;
STAR            : '*' ;
SLASH           : '/' ;
LPAREN          : '(' ;
RPAREN          : ')' ;
COMMA           : ',' ;
COLON           : ':' ;

// Value terminals — DECIMAL must come before NUMBER and DOT
DECIMAL         : [0-9]+ '.' [0-9]+ ;
NUMBER          : [0-9]+ ;
PSEUDO_TEXT     : '==' .*? '==' ;
NAME            : [A-Z] ([A-Z0-9] ([A-Z0-9\-]* [A-Z0-9])?)? ;
SQL_IDENT       : [A-Z] [A-Z0-9_]* ;
STRING_LIT      : '"' ~["]* '"' | '\'' ~[']* '\'' ;
DOT             : '.' ;

WS              : [ \t\r\n]+ -> skip ;
