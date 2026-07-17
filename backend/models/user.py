class User:
    def __init__(self, id=None, nom=None, email=None, poste=None, departement=None, role=None):
        self.id = id
        self.nom = nom
        self.email = email
        self.poste = poste
        self.departement = departement
        self.role = role

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "email": self.email,
            "poste": self.poste,
            "departement": self.departement,
            "role": self.role,
        }
