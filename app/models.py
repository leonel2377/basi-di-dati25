from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from app import db

# Tabella di relazione N:M tra Biglietti ed Extra
biglietti_extra = db.Table('biglietti_extra',
    db.Column('id_biglietto', db.Integer, db.ForeignKey('biglietti.id_biglietto', ondelete='CASCADE'), primary_key=True),
    db.Column('id_extra', db.Integer, db.ForeignKey('extra.id_extra', ondelete='CASCADE'), primary_key=True)
)


class CompagniaAerea(UserMixin, db.Model):
    """
    CompagniaAerea - Entità principale per le compagnie aeree con autenticazione
    Schema: idCompagnia (PK), Nome, CodiceIATA (unique), Paese, Email, Password
    Nota: usiamo 'id' come PK per compatibilità con Flask-Login, ma rappresenta idCompagnia
    """
    __tablename__ = 'compagnie_aeree'
    
    id = db.Column(db.Integer, primary_key=True)  # Rappresenta idCompagnia nello schema
    nome = db.Column(db.String(100), nullable=False)
    codice_iata = db.Column(db.String(3), unique=True, nullable=False, index=True)
    paese = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Relationships
    voli = db.relationship('Volo', backref='compagnia', lazy='dynamic', cascade='all, delete-orphan')
    aerei = db.relationship('Aereo', backref='compagnia', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return a unique ID with type prefix for Flask-Login"""
        return f'c-{self.id}'
    
    def __repr__(self):
        return f'<CompagniaAerea {self.nome} ({self.codice_iata})>'


class Aereo(db.Model):
    """
    Aereo - Entità per gli aeromobili
    Schema: idAereo (PK), Modello, PostiTotali, idCompagnia (FK)
    """
    __tablename__ = 'aerei'
    
    id_aereo = db.Column(db.Integer, primary_key=True)
    modello = db.Column(db.String(50), nullable=False)
    posti_totali = db.Column(db.Integer, nullable=False)
    id_compagnia = db.Column(db.Integer, db.ForeignKey('compagnie_aeree.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    voli = db.relationship('Volo', backref='aereo', lazy='dynamic', cascade='all, delete-orphan')
    
    # Vincoli
    __table_args__ = (
        db.CheckConstraint('posti_totali > 0', name='check_posti_totali_positivi'),
    )
    
    def __repr__(self):
        return f'<Aereo {self.modello}>'


class Aeroporto(db.Model):
    """
    Aeroporto - Entità per gli aeroporti
    Schema: idAeroporto (PK), Nome, Città, Paese, CodiceIATA (unique)
    """
    __tablename__ = 'aeroporti'
    
    id_aeroporto = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    città = db.Column(db.String(100), nullable=False, index=True)
    paese = db.Column(db.String(100), nullable=False)
    codice_iata = db.Column(db.String(3), unique=True, nullable=False, index=True)
    
    # Relationships
    voli_partenza = db.relationship('Volo', foreign_keys='Volo.aeroporto_partenza', backref='aeroporto_partenza_obj', lazy='dynamic')
    voli_destinazione = db.relationship('Volo', foreign_keys='Volo.aeroporto_destinazione', backref='aeroporto_destinazione_obj', lazy='dynamic')
    
    def __repr__(self):
        return f'<Aeroporto {self.città} ({self.codice_iata})>'


class Volo(db.Model):
    """
    Volo - Entità per i voli
    Schema: idVolo (PK), DataPartenza, OraPartenza, DataArrivo, OraArrivo, 
            PostiDisponibili, idCompagnia (FK), idAereo (FK), 
            AeroportoPartenza (FK), AeroportoDestinazione (FK)
    Aggiunto: Prezzi per classe (economy, business, first)
    """
    __tablename__ = 'voli'
    
    id_volo = db.Column(db.Integer, primary_key=True)
    data_partenza = db.Column(db.Date, nullable=False, index=True)
    ora_partenza = db.Column(db.Time, nullable=False)
    data_arrivo = db.Column(db.Date, nullable=False, index=True)
    ora_arrivo = db.Column(db.Time, nullable=False)
    posti_disponibili = db.Column(db.Integer, nullable=False)
    id_compagnia = db.Column(db.Integer, db.ForeignKey('compagnie_aeree.id', ondelete='CASCADE'), nullable=False, index=True)
    id_aereo = db.Column(db.Integer, db.ForeignKey('aerei.id_aereo', ondelete='CASCADE'), nullable=False, index=True)
    aeroporto_partenza = db.Column(db.Integer, db.ForeignKey('aeroporti.id_aeroporto'), nullable=False, index=True)
    aeroporto_destinazione = db.Column(db.Integer, db.ForeignKey('aeroporti.id_aeroporto'), nullable=False, index=True)
    
    # Prezzi per classe (gestiti dalla compagnia)
    prezzo_economy = db.Column(db.Numeric(10, 2), nullable=False)
    prezzo_business = db.Column(db.Numeric(10, 2), nullable=False)
    prezzo_first = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationships
    biglietti = db.relationship('Biglietto', backref='volo', lazy='dynamic', cascade='all, delete-orphan')
    
    # Vincoli e indici
    __table_args__ = (
        db.Index('idx_volo_data_partenza', 'data_partenza'),
        db.Index('idx_volo_aeroporti', 'aeroporto_partenza', 'aeroporto_destinazione'),
        db.CheckConstraint('posti_disponibili >= 0', name='check_posti_disponibili_non_negativi'),
        db.CheckConstraint('aeroporto_partenza != aeroporto_destinazione', name='check_aeroporti_diversi'),
        db.CheckConstraint('prezzo_economy > 0', name='check_prezzo_economy_positivo'),
        db.CheckConstraint('prezzo_business > 0', name='check_prezzo_business_positivo'),
        db.CheckConstraint('prezzo_first > 0', name='check_prezzo_first_positivo'),
        # Vincolo temporale: arrivo deve essere dopo partenza
        # Questo sarà gestito a livello applicativo o con trigger
    )
    
    @property
    def datetime_partenza(self):
        """Combina data e ora partenza in datetime per facilità d'uso"""
        return datetime.combine(self.data_partenza, self.ora_partenza)
    
    @property
    def datetime_arrivo(self):
        """Combina data e ora arrivo in datetime per facilità d'uso"""
        return datetime.combine(self.data_arrivo, self.ora_arrivo)
    
    def __repr__(self):
        return f'<Volo {self.id_volo}>'


class Passeggero(UserMixin, db.Model):
    """
    Passeggero - Entità per i passeggeri (con autenticazione integrata)
    Schema: idPasseggero (PK), Nome, Cognome, Email (unique), Password
    Nota: usiamo 'id' come PK per compatibilità con Flask-Login, ma rappresenta idPasseggero
    """
    __tablename__ = 'passeggeri'
    
    id = db.Column(db.Integer, primary_key=True)  # Rappresenta idPasseggero nello schema
    nome = db.Column(db.String(50), nullable=False)
    cognome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Relationships
    biglietti = db.relationship('Biglietto', backref='passeggero', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return a unique ID with type prefix for Flask-Login"""
        return f'p-{self.id}'
    
    def __repr__(self):
        return f'<Passeggero {self.nome} {self.cognome}>'


class Biglietto(db.Model):
    """
    Biglietto - Entità per i biglietti
    Schema: idBiglietto (PK), DataAcquisto, Prezzo, Classe, Posto,
            idPasseggero (FK), idVolo (FK)
    """
    __tablename__ = 'biglietti'
    
    id_biglietto = db.Column(db.Integer, primary_key=True)
    data_acquisto = db.Column(db.Date, nullable=False, default=date.today, index=True)
    prezzo = db.Column(db.Numeric(10, 2), nullable=False)
    classe = db.Column(db.String(20), nullable=False)  # economy, business, first
    posto = db.Column(db.String(10), nullable=True)  # es. "12A"
    id_passeggero = db.Column(db.Integer, db.ForeignKey('passeggeri.id', ondelete='CASCADE'), nullable=False, index=True)
    id_volo = db.Column(db.Integer, db.ForeignKey('voli.id_volo', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    extra = db.relationship('Extra', secondary=biglietti_extra, lazy='dynamic', backref=db.backref('biglietti', lazy='dynamic'))
    
    # Vincoli
    __table_args__ = (
        db.CheckConstraint('prezzo > 0', name='check_prezzo_positivo'),
        db.CheckConstraint("classe IN ('economy', 'business', 'first')", name='check_classe_valida'),
    )
    
    def __repr__(self):
        return f'<Biglietto {self.id_biglietto}>'


class Extra(db.Model):
    """
    Extra - Entità per i servizi aggiuntivi
    Schema: idExtra (PK), Nome, Costo
    """
    __tablename__ = 'extra'
    
    id_extra = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    costo = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Vincoli
    __table_args__ = (
        db.CheckConstraint('costo > 0', name='check_costo_positivo'),
    )
    
    def __repr__(self):
        return f'<Extra {self.nome}>'
