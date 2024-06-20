from . import db

class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, unique=False)
    end = db.Column(db.DateTime, unique=False)
    eventName = db.Column(db.String, unique=True)
    showNumber = db.Column(db.Integer, unique=True)
    accountManager = db.Column(db.String, unique=False)
    location = db.Column(db.String, unique=False)

    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'))

    def __repr__(self):
        return '<Shift %r %r>' % self.showNumber, self.eventName
    
class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    worker = db.Column(db.String, unique=True)
    rate = db.Column(db.Float, unique=False)
    

    shifts = db.relationship('Shift', backref='worker')

    def __repr__(self):
        return '<Worker %r $r>' % self.worker, self.rate