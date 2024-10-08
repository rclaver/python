#!/usr/bin/python3
# -*- coding: utf-8 -*-

def application(environ, start_response):
	if (environ["PATH_INFO"] == "/"):
		respuesta = "<p>Página inicial</p>"
		respuesta += "<p><a href='/suma'>súmate algo</a></p>"
		respuesta += "<p><a href='/suma?a=3&b=5'>súmate 3 + 5</a></p>"
	elif (environ["PATH_INFO"] == "/suma"):
		params = environ["QUERY_STRING"].split("&")
		suma = 0
		if (params != ['']):
			for par in params:
				suma += int(par.split("=")[1])
		respuesta = "<p>parámetros: %s.</p>" % params
		respuesta += "<p>La suma es %d</p>" % suma
	else:
		respuesta = "<p><strong>Página incorrecta</strong></p>"

	start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
	return [respuesta.encode()]

if (__name__ == '__main__'):
	from wsgiref.simple_server import make_server
	srv = make_server('localhost', 8080, application)
	srv.serve_forever()
