from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from app.models import Passeggero, CompagniaAerea

class LoginForm(FlaskForm):
    """Login form per passeggeri e compagnie"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('Tipo Utente', choices=[('passeggero', 'Passeggero'), ('compagnia', 'Compagnia Aerea')], validators=[DataRequired()])
    submit = SubmitField('Accedi')


class RegistrationForm(FlaskForm):
    """Registrazione form per passeggeri"""
    nome = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')
    
    def validate_email(self, email):
        # Normalize email to lowercase
        email_lower = email.data.lower() if email.data else ''
        # Check both passeggeri and compagnie_aeree
        passeggero = Passeggero.query.filter_by(email=email_lower).first()
        compagnia = CompagniaAerea.query.filter_by(email=email_lower).first()
        if passeggero or compagnia:
            raise ValidationError('Email già registrata. Usa un\'altra email.')
        # Update email field to lowercase
        email.data = email_lower


class CompagniaAereaRegistrationForm(FlaskForm):
    """Form per registrazione compagnia aerea"""
    nome = StringField('Nome Compagnia', validators=[DataRequired(), Length(max=100)])
    codice_iata = StringField('Codice IATA', validators=[DataRequired(), Length(min=2, max=3)])
    paese = StringField('Paese', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrati')
    
    def validate_email(self, email):
        # Normalize email to lowercase
        email_lower = email.data.lower() if email.data else ''
        # Check both passeggeri and compagnie_aeree
        passeggero = Passeggero.query.filter_by(email=email_lower).first()
        compagnia = CompagniaAerea.query.filter_by(email=email_lower).first()
        if passeggero or compagnia:
            raise ValidationError('Email già registrata. Usa un\'altra email.')
        # Update email field to lowercase
        email.data = email_lower
    
    def validate_codice_iata(self, codice_iata):
        compagnia = CompagniaAerea.query.filter_by(codice_iata=codice_iata.data.upper()).first()
        if compagnia:
            raise ValidationError('Codice IATA già utilizzato.')


class CompagniaAereaForm(FlaskForm):
    """Form per modificare compagnia aerea"""
    nome = StringField('Nome Compagnia', validators=[DataRequired(), Length(max=100)])
    codice_iata = StringField('Codice IATA', validators=[DataRequired(), Length(min=2, max=3)])
    paese = StringField('Paese', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Salva')


class AereoForm(FlaskForm):
    """Form per creare/modificare aereo"""
    modello = StringField('Modello', validators=[DataRequired(), Length(max=50)])
    posti_totali = IntegerField('Posti Totali', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Salva')


class AeroportoForm(FlaskForm):
    """Form per creare/modificare aeroporto"""
    nome = StringField('Nome', validators=[DataRequired(), Length(max=200)])
    città = StringField('Città', validators=[DataRequired(), Length(max=100)])
    paese = StringField('Paese', validators=[DataRequired(), Length(max=100)])
    codice_iata = StringField('Codice IATA', validators=[DataRequired(), Length(min=2, max=3)])
    submit = SubmitField('Salva')


class VoloForm(FlaskForm):
    """Form per creare/modificare volo"""
    data_partenza = DateField('Data Partenza', validators=[DataRequired()])
    ora_partenza = TimeField('Ora Partenza', validators=[DataRequired()])
    data_arrivo = DateField('Data Arrivo', validators=[DataRequired()])
    ora_arrivo = TimeField('Ora Arrivo', validators=[DataRequired()])
    posti_disponibili = IntegerField('Posti Disponibili', validators=[NumberRange(min=0)])
    id_aereo = SelectField('Aereo', coerce=int, validators=[DataRequired()])
    aeroporto_partenza = SelectField('Aeroporto Partenza', coerce=int, validators=[DataRequired()])
    aeroporto_destinazione = SelectField('Aeroporto Destinazione', coerce=int, validators=[DataRequired()])
    prezzo_economy = DecimalField('Prezzo Economy', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    prezzo_business = DecimalField('Prezzo Business', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    prezzo_first = DecimalField('Prezzo First Class', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    submit = SubmitField('Salva')
    
    def validate_aeroporto_destinazione(self, aeroporto_destinazione):
        if aeroporto_destinazione.data == self.aeroporto_partenza.data:
            raise ValidationError('Aeroporto di partenza e destinazione devono essere diversi.')
    
    def validate_data_arrivo(self, data_arrivo):
        if data_arrivo.data and self.data_partenza.data:
            if data_arrivo.data < self.data_partenza.data:
                raise ValidationError('La data di arrivo deve essere dopo la data di partenza.')
    
    def validate_ora_arrivo(self, ora_arrivo):
        if (ora_arrivo.data and self.ora_partenza.data and 
            self.data_arrivo.data and self.data_partenza.data):
            if self.data_arrivo.data == self.data_partenza.data:
                from datetime import datetime
                dt_partenza = datetime.combine(self.data_partenza.data, self.ora_partenza.data)
                dt_arrivo = datetime.combine(self.data_arrivo.data, ora_arrivo.data)
                if dt_arrivo <= dt_partenza:
                    raise ValidationError('L\'ora di arrivo deve essere dopo l\'ora di partenza.')


class FlightSearchForm(FlaskForm):
    """Form per ricerca voli"""
    aeroporto_partenza = SelectField('Aeroporto Partenza', coerce=int, validators=[DataRequired()])
    aeroporto_destinazione = SelectField('Aeroporto Destinazione', coerce=int, validators=[DataRequired()])
    data_partenza = DateField('Data Partenza', validators=[DataRequired()])
    submit = SubmitField('Cerca Voli')
    
    def validate_aeroporto_destinazione(self, aeroporto_destinazione):
        if aeroporto_destinazione.data == self.aeroporto_partenza.data:
            raise ValidationError('Aeroporto di partenza e destinazione devono essere diversi.')


class BigliettoForm(FlaskForm):
    """Form per acquisto biglietto"""
    classe = SelectField('Classe', choices=[('economy', 'Economy'), ('business', 'Business'), ('first', 'First Class')], validators=[DataRequired()])
    posto = StringField('Posto', validators=[Length(max=10)])
    submit = SubmitField('Acquista Biglietto')


class PassengerProfileForm(FlaskForm):
    """Form per modifica profilo passeggero"""
    nome = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Salva Modifiche')


class LogoutForm(FlaskForm):
    """Form per logout con protezione CSRF"""
    submit = SubmitField('Logout')


class PasswordResetRequestForm(FlaskForm):
    """Form per richiesta reset password"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_type = SelectField(
        'Tipo Utente',
        choices=[('passeggero', 'Passeggero'), ('compagnia', 'Compagnia Aerea')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Invia Link Reset')


class PasswordResetForm(FlaskForm):
    """Form per reset password"""
    password = PasswordField('Nuova Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Ripeti Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reimposta Password')