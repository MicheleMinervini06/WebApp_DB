-- ===========================================
-- Type Definitions
-- ===========================================

-- Type for Employee
CREATE OR REPLACE TYPE EmployeeType AS OBJECT (
    phiscal_code    NUMBER,
    name            VARCHAR2(100),
    surname         VARCHAR2(100),
    role            VARCHAR2(50)
);
/

-- VARRAY Type for Employee
CREATE OR REPLACE TYPE EmployeeRefArray AS VARRAY(8) OF REF EmployeeType;
/

-- Type for Team
CREATE OR REPLACE TYPE TeamType AS OBJECT (
    team_id         NUMBER,
    name            VARCHAR2(100),
    num_operations  NUMBER,
    performance_score NUMBER(4,2),  -- Renamed to clarify its purpose
    employees       EmployeeRefArray
);
/

-- Table of TeamType
CREATE OR REPLACE TYPE TeamTable AS TABLE OF TeamType;
/

-- Type for Team References
CREATE OR REPLACE TYPE TeamRefArray AS VARRAY(100) OF REF TeamType;
/

-- Type for OperationalCenter
CREATE OR REPLACE TYPE OperationalCenterType AS OBJECT (
    center_id       NUMBER,
    name            VARCHAR2(100),
    address         VARCHAR2(255),
    city            VARCHAR2(100),
    province        VARCHAR2(50),
    teams           TeamRefArray
);
/

-- Table of OperationalCenterType
CREATE OR REPLACE TYPE OperationalCenterTable AS TABLE OF OperationalCenterType;
/

-- Type for BusinessAccount
CREATE OR REPLACE TYPE BusinessAccountType AS OBJECT (
    accountCode            NUMBER,
    creation_date   DATE
);
/

-- Create BusinessAccountRefArray type
CREATE OR REPLACE TYPE BusinessAccountRefArray AS VARRAY(10) OF REF BusinessAccountType;
/

-- Nested Table Type for BusinessAccount
CREATE OR REPLACE TYPE BusinessAccountTable AS TABLE OF BusinessAccountType;
/

-- Type for Order
CREATE OR REPLACE TYPE OrderType AS OBJECT (
    order_num           NUMBER,
    order_type         VARCHAR2(20),
    order_date         DATE,
    expected_date      DATE,
    cost               NUMBER,
    placement_modality VARCHAR2(50),
    team               REF TeamType,
    employees          EmployeeRefArray,
    account            REF BusinessAccountType
) NOT FINAL;
/

-- Type for ActiveOrder
CREATE TYPE ActiveOrderType UNDER OrderType (
    state           VARCHAR2(20)
);
/

-- Type for CompletedOrder
CREATE OR REPLACE TYPE CompletedOrderType UNDER OrderType (
    completion_date  DATE,
    feedback         INTEGER
);
/

-- Type for Customer
CREATE OR REPLACE TYPE CustomerType AS OBJECT (
    customer_id     NUMBER,
    email           VARCHAR2(100),
    phone           VARCHAR2(20),  -- Increased size to accommodate international numbers
    accounts        BusinessAccountRefArray
) NOT FINAL;
/

-- Type for Individual
CREATE OR REPLACE TYPE IndividualType UNDER CustomerType (
    name            VARCHAR2(100),
    surname         VARCHAR2(100),
    dob             DATE
);
/

-- Type for Business
CREATE OR REPLACE TYPE BusinessType UNDER CustomerType (
    company_name    VARCHAR2(100),
    vat_number      VARCHAR2(20)
);
/