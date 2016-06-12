
import bottle

class WebIf():

    myurl = '/status'

    def __init__(self):
        bottle.run(host='localhost', port=80, debug=True)


    @bottle.get(myurl)
    def hello():
        return 'Hello World'

    @bottle.error(404)
    def error404(error):
        return 'error 404'