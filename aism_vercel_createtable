CREATE TABLE aism_accounts (
	id  SERIAL PRIMARY KEY,
	line_id VARCHAR ( 50 ) NOT NULL UNIQUE,
	user_name VARCHAR ( 50 ) NULL, 
	created_on TIMESTAMP NOT NULL
);

CREATE TABLE aism_pay (
	id  SERIAL PRIMARY KEY,
	line_id VARCHAR ( 50 ) NOT NULL, 
	order_id VARCHAR ( 50 ) NOT NULL,
	rtnmsg VARCHAR ( 100 ) NULL,	
	created_on TIMESTAMP NOT NULL	
);
