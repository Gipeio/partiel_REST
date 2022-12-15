from flask import Flask, jsonify, abort, request
import mariadb
import urllib.parse

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False  # pour utiliser l'UTF-8 plutot que l'unicode


def execute_query(query, data=()):
    config = {
        'host': 'mariadb',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'mydatabase'
    }
    """Execute une requete SQL avec les param associés"""
    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL statement
    cur.execute(query, data)

    if cur.description:
        # serialize results into JSON
        row_headers = [x[0] for x in cur.description]
        rv = cur.fetchall()
        list_result = []
        for result in rv:
            list_result.append(dict(zip(row_headers, result)))
        return list_result
    else:
        conn.commit()
        return cur.lastrowid


# we define the route /
@app.route('/')
def welcome():
    liens = [{}]
    liens[0]["_links"] = [{
        "href": "/groupes",
        "rel": "groupes"
    }, {
        "href": "/concerts",
        "rel": "concerts"
    },
    {
        "href": "/billets",
        "rel": "billets"
    }]
    return jsonify(liens), 200

#################################### GROUPES ################################

@app.route('/groupes', methods=['POST'])
def post_pays():
    """"Ajoute un groupe"""
    nom = request.args.get("nom")
    execute_query("insert into groupes (nom) values (?)", (nom,))
    # on renvoi le lien du groupes que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/groupes/" + urllib.parse.quote(nom),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

# @app.route('/groupes/<string:nom>/concerts')
# def get_concerts_from_groupes(nom):
#     """recupère les concerts d'un groupe"""
#     concerts = execute_query("""select concerts.id
#                                     from concerts
#                                     join groupes on concerts.groupe_id = groupes.id
#                                     where lower(groupes.nom) = ?""", (urllib.parse.unquote(nom.lower()),))
#     if concerts == []:
#         abort(404, "Aucune concerts pour ce groupe")
#     # ajout de _links à chaque dico pays
#     for i in range(len(regions)):
#         regions[0]["_links"] = [
#             {
#                 "href": "/concerts/" + urllib.parse.quote(concerts[i]["nom"]),
#                 "rel": "self"
#             },
#             {
#                 "href": "/concerts/" + urllib.parse.quote(concerts[i]["nom"]) + "/departements",
#                 "rel": "departements"
#             }
#         ]
#     return jsonify(regions), 200

@app.route('/groupes')
def get_groupes():
    """recupère la liste des groupes"""
    groupes = execute_query("select nom from groupes")
    # ajout de _links à chaque dico groupes
    for i in range(len(groupes)):
        groupes[i]["_links"] = [
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[i]["nom"]),
                "rel": "self"
            },
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[i]["nom"]) + "/concerts",
                "rel": "concerts"
            }
        ]
    return jsonify(groupes), 200

@app.route('/groupes/<string:nom>')
def get_groupes_by_name(nom):
    """recupère un groupe parmis la liste des groupes"""
    groupes = execute_query("select nom from groupes where nom=?",(nom,))
    # ajout de _links à chaque dico groupes
    groupes[0]["_links"] = [
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[0]["nom"]),
                "rel": "self"
            },
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[0]["nom"]) + "/concerts",
                "rel": "concerts"
            }
        ]
    return jsonify(groupes), 200

@app.route('/groupes/<string:nom>', methods=['DELETE'])
def delete_groupes_by_name(nom):
    """supprime un groupe parmis la liste des groupes"""
    groupes = execute_query("delete from groupes where nom=?",(nom,))
    return "", 204  # no data

#################################### CONCERTS ################################

@app.route('/groupes/<string:groupe>/concerts', methods=['POST'])
def post_concert(groupe):
    """"Ajoute un concert"""
    date = request.args.get("date")
    duree = request.args.get("duree")
    places = request.args.get("places")

    execute_query("insert into concerts (date, durée, place_disponible,groupe_id) values (?,?,?,(select id from groupes where nom = ?))", (date, duree, places,groupe))
    # on renvoi le lien de la région que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/concerts/" + urllib.parse.quote(date),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created


@app.route('/concerts')
def get_concerts():
    """recupère la liste des concerts"""
    concerts = execute_query("select * from concerts")
    # ajout de _links à chaque dico concerts
    for i in range(len(concerts)):
        concerts[i]["_links"] = [
            {
                "href": "/concerts/" + urllib.parse.quote(concerts[i]["date"]),
                "rel": "self"
            }
        ]
    return jsonify(concerts), 200

@app.route('/concerts/<string:date>')
def get_concert_by_date(date):
    """"Récupère les infos d'un concert en paramètre"""
    concert = execute_query("select * from concerts where date=?", (date,))
    # ajout de _links au concert 
    concert[0]["_links"] = [{
        "href": "/concerts/" + urllib.parse.quote(concert[0]["date"]),
        "rel": "concerts"
    }]
    return jsonify(concert), 200

@app.route('/groupes/<string:groupe>/concerts')
def get_concert_by_groupe(groupe):
    """"Récupère les infos d'un concert en paramètre"""
    concert = execute_query("select * from concerts join groupes on concerts.groupe_id=groupes.id where groupes.nom=?", (groupe,))
    # ajout de _links au concert 
    for i in range(len(concert)):
        concert[i]["_links"] = [{
        "href": "/concerts/" + urllib.parse.quote(concert[i]["date"]),
        "rel": "concerts"
    }]
    return jsonify(concert), 200

@app.route('/concerts/<string:date>', methods=['DELETE'])
def delete_concerts(date):
    """supprimer un concert"""
    # join groupes on concerts.groupe_id = groupes.id
#                                     where lower(groupes.nom) = ?""", (urllib.parse.unquote(nom.lower()),))
    execute_query("delete from concerts where date= ?", (date,))
    return "", 204  # no data

########################## BILLETS ##################
@app.route('/concerts/<string:concert>/billets', methods=['POST'])
def post_billet(concert):
    """"Ajoute un concert"""
    nom = request.args.get("nom")
    prenom = request.args.get("prenom")
    mail = request.args.get("mail")

    execute_query("insert into billets (nom, prenom, mail,concert_id) values (?,?,?,(select id from concerts where date = ?))", (nom, prenom, mail,concert))
    # on renvoi le lien de la région que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/billets/" + urllib.parse.quote(mail),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

@app.route('/billets/<string:mail>')
def get_billets(mail):
    """Récupère les infos d'une ville en envoyant une requete HTTP
       Si la ville n'existe pas renvoi 404
    """
    billets = execute_query("select * from billets where mail = ?", (mail,))
    if billets == []:
        abort(404, "Ce billet n'existe pas")
    billets[0]["_links"] = [{
            "href": "/billets/" + billets[0]["mail"],
            "rel": "self"
        }]
    return jsonify(billets), 200

# @app.route('/billets')
# def get_billets():
#     """Récupère les infos d'une ville en envoyant une requete HTTP
#        Si la ville n'existe pas renvoi 404
#     """
#     billets = execute_query("select * from billets", ())
#     if billets == []:
#         abort(404, "Ce billet n'existe pas")
#     billets[0]["_links"] = [{
#             "href": "/billets/" + billets[0]["mail"],
#             "rel": "self"
#         }]
#     return jsonify(billets), 200

@app.route('/billets/<string:mail>', methods=['DELETE'])
def delete_billets(mail):
   
    execute_query("delete from billets where mail = ?", (mail,))
    return "", 204


if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
