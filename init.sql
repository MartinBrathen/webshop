USE webshopDB;

CREATE TABLE IF NOT EXISTS Products(
    pName varchar(32),
    stock int,
    price int,
    descr varchar(255),
    pic varchar(255),
    discontinued bit DEFAULT 0,
    ID int auto_increment,
    PRIMARY KEY (ID)
);

CREATE TABLE IF NOT EXISTS Users(
    fName varchar(32),
    lName varchar(32),
    email varchar(64),
    pWord varchar(64),
    adress varchar(64),
    country varchar(32),
    phone varchar(32),
    admin bit DEFAULT 0,
    ID int auto_increment,
    PRIMARY KEY (ID)
);

CREATE TABLE IF NOT EXISTS Basket(
    userID int,
    productID int,
    amount int,
	CHECK (amount > 0)
    PRIMARY KEY (userID, productID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Orders(
    ID int auto_increment,
    orderStatus varchar(32),
    orderDate DATE DEFAULT GETDATE,
    userID int,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID)
);

CREATE TABLE IF NOT EXISTS Transactions(
    productID int,
    amount int,
    ID int auto_increment,
    orderID int,
    cost int,
    PRIMARY KEY (ID),
    FOREIGN KEY (orderID) REFERENCES Orders(ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Comments(
    commentS varchar(256),
    userID int,
    productID int,
    ID int auto_increment,
	tStamp TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Ratings(
    rating bit,
    userID int,
    productID int,
    PRIMARY KEY(userID,productID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Keywords(
    keyword varchar(32),
    ID int auto_increment,
    PRIMARY KEY(ID)
);


CREATE TABLE IF NOT EXISTS KeywordRelation(
    productID int,
    keywordID int,
    PRIMARY KEY(keywordID, productID),
    FOREIGN KEY (keywordID) REFERENCES Keywords(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);
