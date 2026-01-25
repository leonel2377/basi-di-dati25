import os
from app import create_app, db
from app.models import CompagniaAerea, Aeroporto, Aereo, Volo, Passeggero, Biglietto, Extra

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'CompagniaAerea': CompagniaAerea, 'Aeroporto': Aeroporto, 
            'Aereo': Aereo, 'Volo': Volo, 'Passeggero': Passeggero, 
            'Biglietto': Biglietto, 'Extra': Extra}

if __name__ == '__main__':
    debug_enabled = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    app.run(debug=debug_enabled)

