USE webshopDB;

CREATE TABLE IF NOT EXISTS Products(
    pName varchar(32),
    stock int,
    price int,
    descr varchar(255),
    pic varchar(255),
    ID int,
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
    admin bit,
    ID int,
    PRIMARY KEY (ID)
);

CREATE TABLE IF NOT EXISTS Basket(
    userID int,
    productID int,
    amount int,
    ID int,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Orders(
    ID int,
    orderStatus varchar(32),
    orderDate DATE,
    userID int,
    PRIMARY KEY (ID),
    FOREIGN KEY (userID) REFERENCES Users(ID)
);

CREATE TABLE IF NOT EXISTS Transactions(
    userID int,
    productID int,
    amount int,
    ID int,
	orderID int,
    PRIMARY KEY (ID),
    FOREIGN KEY (orderID) REFERENCES Orders(ID),
    FOREIGN KEY (userID) REFERENCES Users(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);

CREATE TABLE IF NOT EXISTS Comments(
    comments varchar(256),
    userID int,
    productID int,
    ID int,
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
    ID int,
    PRIMARY KEY(ID)
);


CREATE TABLE IF NOT EXISTS KeywordRelation(
    ID int,
    productID int,
    keywordID int,
    PRIMARY KEY(ID),
    FOREIGN KEY (keywordID) REFERENCES Keywords(ID),
    FOREIGN KEY (productID) REFERENCES Products(ID)
);
