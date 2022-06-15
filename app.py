from flask import Flask
from flask_cors import CORS, cross_origin
from flaskext.mysql import MySQL

from send import *
import pymysql
from flask import jsonify
from flask import flash, request

app = Flask(__name__)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'DATABASE_USERNAME'
app.config['MYSQL_DATABASE_PASSWORD'] = 'DATABASE_USER_PASS'
app.config['MYSQL_DATABASE_DB'] = 'DATABASE_NAME'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

def create_queue(_message, _phone, _port_id, _status = 1):
    try:        
        if _message and _phone and _port_id and request.method == 'POST':
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)		
            sqlQuery = "INSERT INTO queue(message, phone, status, port_id) VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE message="+_message+", phone="+_phone+", status="+str(_status)+", port_id="+str(_port_id)+""
            bindData = (_message, _phone,_status, _port_id)            
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            return cursor.lastrowid
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close()

def update_queue(_id, _message, _phone, _status, _port_id):
    try:
        if _message and _phone and _id:			
            sqlQuery = "UPDATE queue SET message=%s, phone=%s, status=%s, port_id=%s WHERE id=%s"
            bindData = (_message, _phone, _status, _port_id, _id,)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

def delete_queue(_id):
    try:
        if _id:
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM queue WHERE id =%s", (_id,))
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

def best_port():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM ports WHERE enable = 1 ORDER BY successfull_attempt desc, recent_failed_attempt asc LIMIT 1;")
        queueRow = cursor.fetchone()
        return queueRow
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close()

def update_port(_id, _atempt):
    try:
        if _id:
            if _atempt:
                sqlQuery = "UPDATE ports SET recent_failed_attempt = 0, successfull_attempt = successfull_attempt+1 WHERE id=%s"
            else:
                sqlQuery = "UPDATE ports SET recent_failed_attempt = recent_failed_attempt+1, successfull_attempt = 0 WHERE id=%s"
            bindData = (_id)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@app.route('/send', methods=['POST'])
def send_OTP():
    try:        
        _json = request.json
        _message = _json['message']
        _phone = _json['phone']

        if _message and _phone and request.method == 'POST':
            port_row = best_port()
            _port_id = port_row['id']
            _serial_address = port_row['serial_address']
            row_id = create_queue(_message, _phone, _port_id)
            if row_id:
                send_result = send_sms(_serial_address, _phone, _message)
                if send_result:
                    delete_queue(row_id)
                    update_port(_port_id, True)
                    respone = jsonify('OTP code sent successfully!')
                    respone.status_code = 200
                    return respone
                else:
                    update_queue(row_id, _message, _phone, 0, _port_id)
                    update_port(_port_id, False)
                    respone = jsonify('sms server error!')
                    respone.status_code = 200
                    return respone
            else:
                return showMessage()
        else:
            return showMessage()
    except Exception as e:
        print(e)
        

@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    respone = jsonify(message)
    respone.status_code = 404
    return respone
        
if __name__ == "__main__":
    app.run()