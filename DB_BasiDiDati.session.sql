USE viaggiAerei;
 
CREATE TABLE CompagnieAeree (
    ID_Compagnia SERIAL PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL,
    Codice_IATA VARCHAR(5) NOT NULL UNIQUE,
    Paese VARCHAR(50) NOT NULL
);

CREATE TABLE Aeroporti (
    ID_aeroporto SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    citta VARCHAR(50) NOT NULL,
    paese VARCHAR(50) NOT NULL,
    Codice_IATA VARCHAR(5) NOT NULL UNIQUE
);

CREATE TABLE Voli (
ID_volo SERIAL PRIMARY KEY,
data_partenza DATE NOT NULL,
ora_partenza TIME NOT NULL,
data_arrivo DATA NOT NULL,
ora_arrivo TIME NOT NULL,
posti_disponibili INT NOT NULL CHECK(posti_disponibili >= 0),
ID_Compagnia INT NOT NULL,
ID_aeroporto INT NOT NULL,
AEROPORTO_partenza INT NOT NULL,
AEROPORTO_arrivo INT NOT NULL,
FOREIGN KEY (ID_Compagnia) REFERENCES CompagnieAeree(ID_Compagnia),
FOREIGN KEY(ID_aereo) REFERENCES Aerei(ID_aereo),
FOREIGN KEY (AEROPORTO_partenza) REFERENCES Aeroporti(ID_aeroporto),
FOREIGN KEY(AEROPORTO_arrivo) REFERENCES Aeroporti(ID_aeroporto),
CHECK ( (data_arrivo > data_partenza)OR (data_arrivo = data_partenza AND ora_arrivo > ora_partenza)) 
);

CREATE TABLE Passeggeri (
    ID_passeggero SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    cognome VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,

);

CREATE TABLE Biglietti (
    ID_biglietto SERIAL PRIMARY KEY,
    data_acquisto DATE NOT NULL,
    prezzo NUMERIC(8,2) NOT NULL CHECK (prezzo > 0),
    classe VARCHAR(10) NOT NULL CHECK (classe IN ('economy', 'business', 'first')),
    post VARCHAR(5) NOT NULL,
    ID_passeggero INT NULL,
    ID_volo INT NOT NULL,
    FOREIGN KEY (ID_passeggero) REFERENCES Passeggeri(ID_passeggero),
    FOREIGN KEY (ID_volo) REFERENCES Voli(ID_volo),
);

CREATE TABLE BigliettiExtra (
    ID_biglietto INT NOT NULL,
    ID_extra INT NOT NULL,
    PRIMARY KEY (ID_biglietto, ID_extra),
    PRIMARY KEY (ID_biglietto) REFERENCES Biglietti(ID_biglietto),
    FOREIGN KEY(ID_extra) REFERENCES Extra(ID_extra)
);

CREATE TABLE Extra(
ID_extra SERIAL PRIMARY KEY,
nome VARCHAR(50) NOT NULL,
costo NUMERIC(6,2) NOT NULL CHECK(costo >= 0)
);