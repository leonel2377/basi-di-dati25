CREATE TABLE compagnie_aeree (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    codice_iata TEXT NOT NULL UNIQUE,
    paese TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE aerei (
    id_aereo SERIAL PRIMARY KEY,
    modello TEXT NOT NULL,
    posti_totali INTEGER NOT NULL CHECK (posti_totali > 0),
    id_compagnia INTEGER NOT NULL,
    FOREIGN KEY (id_compagnia) REFERENCES compagnie_aeree(id) ON DELETE CASCADE
);

CREATE TABLE aeroporti (
    id_aeroporto SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    "città" TEXT NOT NULL,
    paese TEXT NOT NULL,
    codice_iata TEXT NOT NULL UNIQUE
);

CREATE TABLE voli (
    id_volo SERIAL PRIMARY KEY,
    data_partenza DATE NOT NULL,
    ora_partenza TIME NOT NULL,
    data_arrivo DATE NOT NULL,
    ora_arrivo TIME NOT NULL,
    posti_disponibili INTEGER NOT NULL CHECK (posti_disponibili >= 0),
    id_compagnia INTEGER NOT NULL,
    id_aereo INTEGER NOT NULL,
    aeroporto_partenza INTEGER NOT NULL,
    aeroporto_destinazione INTEGER NOT NULL,
    prezzo_economy NUMERIC(10, 2) NOT NULL CHECK (prezzo_economy > 0),
    prezzo_business NUMERIC(10, 2) NOT NULL CHECK (prezzo_business > 0),
    prezzo_first NUMERIC(10, 2) NOT NULL CHECK (prezzo_first > 0),
    FOREIGN KEY (id_compagnia) REFERENCES compagnie_aeree(id) ON DELETE CASCADE,
    FOREIGN KEY (id_aereo) REFERENCES aerei(id_aereo) ON DELETE CASCADE,
    FOREIGN KEY (aeroporto_partenza) REFERENCES aeroporti(id_aeroporto),
    FOREIGN KEY (aeroporto_destinazione) REFERENCES aeroporti(id_aeroporto),
    CHECK (aeroporto_partenza != aeroporto_destinazione)
);

CREATE TABLE passeggeri (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE biglietti (
    id_biglietto SERIAL PRIMARY KEY,
    data_acquisto DATE NOT NULL,
    prezzo NUMERIC(10, 2) NOT NULL CHECK (prezzo > 0),
    classe TEXT NOT NULL CHECK (classe IN ('economy', 'business', 'first')),
    posto TEXT,
    id_passeggero INTEGER NOT NULL,
    id_volo INTEGER NOT NULL,
    FOREIGN KEY (id_passeggero) REFERENCES passeggeri(id) ON DELETE CASCADE,
    FOREIGN KEY (id_volo) REFERENCES voli(id_volo) ON DELETE CASCADE
);

CREATE TABLE extra (
    id_extra SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    costo NUMERIC(10, 2) NOT NULL CHECK (costo > 0)
);

CREATE TABLE biglietti_extra (
    id_biglietto SERIAL NOT NULL,
    id_extra INTEGER NOT NULL,
    PRIMARY KEY (id_biglietto, id_extra),
    FOREIGN KEY (id_biglietto) REFERENCES biglietti(id_biglietto) ON DELETE CASCADE,
    FOREIGN KEY (id_extra) REFERENCES extra(id_extra) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION gestisci_posti_volo()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT posti_disponibili
        FROM Voli
        WHERE id_volo = NEW.id_volo) <= 0 THEN
        RAISE EXCEPTION 'Impossibile acquistare il biglietto: posti esauriti';
    END IF;

    UPDATE Voli
    SET posti_disponibili = posti_disponibili - 1
    WHERE id_volo = NEW.id_volo;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_biglietto_posti
BEFORE INSERT ON biglietti
FOR EACH ROW
EXECUTE FUNCTION gestisci_posti_volo();



