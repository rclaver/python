#!/usr/bin/python
# -*- coding: UTF8 -*-
import os, sys, socket, shutil

C_NONE="\033[0m"
C_CYN="\033[0;36m"  #normal
C_WHT="\033[0;37m"
CB_RED="\033[1;31m" #bold
CB_YLW="\033[1;33m"
CB_WHT="\033[1;37m"
CB_CYN="\033[1;36m"
CB_GRN="\033[1;32m"
U_WHT=C_NONE+"\033[4;37m"   # underline

print(sys.version_info)
print("hostname: "+socket.gethostname())
print(CB_CYN+"==================================================================")
print(CB_CYN+" Obtenció dels links generats dels projectes activityutil")
print(CB_CYN+"=================================================================="+C_NONE)

# Valors per defecte
PREFIX="documents_fp_docencia_activitats_"
if (socket.gethostname() == "LM19"):
	MDPROJECTS="/home/rafael/Vídeos/mdprojects/activitats"
	PAGES="/home/rafael/Vídeos/pages/activitats"
	ACTIVITY_DIR="/home/rafael/Vídeos/ActivityUtil"
else:
	MDPROJECTS="/home/wikidev/wiki18/data/mdprojects/documents_fp/docencia/activitats/"
	PAGES="/home/wikidev/wiki18/data/pages/documents_fp/docencia/activitats/"
	ACTIVITY_DIR="../ActivityUtil"		#/html/FP/Recursos/ActivityUtil

LOG = "../bin/links_sftp_activitats.txt"
ACTUAL_PROJECT = ""

def sintaxi():
	print(CB_WHT+"Sintaxi:")
	print(CB_WHT+"   -f | --file "+U_WHT+"file"+C_WHT+": fitxer amb els paràmetres de configuració")
	print(CB_GRN+"       format del fitxer: "+CB_CYN+"key=\"value\" "+C_WHT+"(1 per línia)")
	print(CB_GRN+"           valors de key: "+CB_CYN+"[mdprojects, pages, activity_dir, prefix]")
	print(CB_YLW+"           el valor de activity_dir ha de començar per "+CB_WHT+"\"./\"")
	print(CB_WHT+"   -m | --mdprojects   "+U_WHT+"valor"+C_WHT+": ruta absoluta de l'arbre de projectes a tractar")
	print(CB_WHT+"   -p | --pages        "+U_WHT+"valor"+C_WHT+": ruta absoluta de l'arbre de pages a tractar")
	print(CB_WHT+"   -d | --activity_dir "+U_WHT+"valor"+C_WHT+": ruta relativa de l'arbre de directoris FTP")
	print(CB_WHT+"   -x | --prefix       "+U_WHT+"valor"+C_WHT+": part del nom de directori corresponent als projectes")
	return

def actualParams():
	global MDPROJECTS, PAGES, ACTIVITY_DIR, PREFIX
	print(CB_RED+"\nEls paràmetres actuals son:"+C_NONE)
	print("  >> mdprojects   = " + CB_YLW + MDPROJECTS + C_NONE)
	print("  >> pages        = " + CB_YLW + PAGES + C_NONE)
	print("  >> activity_dir = " + CB_YLW + ACTIVITY_DIR + C_NONE)
	print("  >> prefix       = " + CB_YLW + PREFIX + C_NONE)
	r = raw_input("\nVols continuar? s/N: ")
	if (r.upper() != "S"): exit()

	r = raw_input("\nVols modificar els paràmetres? s/N: ")
	if (r.upper() == "S"):
		r = raw_input(CB_WHT+"  mdprojects   " +CB_CYN + "(" + MDPROJECTS + ") = " +C_NONE)
		if (r): MDPROJECTS = r
		r = raw_input(CB_WHT+"  pages        " +CB_CYN + "(" +PAGES + ") = " +C_NONE)
		if (r): PAGES = r
		r = raw_input(CB_WHT+"  activity_dir " +CB_CYN + "(" + ACTIVITY_DIR + ") = " +C_NONE)
		if (r): ACTIVITY_DIR = r
		r = raw_input(CB_WHT+"  prefix       " +CB_CYN + "(" + PREFIX + ") = " +C_NONE)
		if (r): PREFIX = r

		actualParams()

# Tratamiento de los argumentos de la línea de comandos
arg = sys.argv[1:]
while arg:
	if (arg[0]=="-f" or arg[0]=="--file"):
		if (os.path.exists(arg[1]+".py")):
			params = __import__(arg[1])
			MDPROJECTS = params.mdprojects
			ACTIVITY_DIR = params.activity_dir
			PREFIX = params.prefix
			break
		else:
			exit()
	elif (arg[0]=="-m" or arg[0]=="--mdprojects"):
		MDPROJECTS = arg[1]
	elif (arg[0]=="-p" or arg[0]=="--pages"):
		PAGES = arg[1]
	elif (arg[0]=="-d" or arg[0]=="--activity_dir"):
		ACTIVITY_DIR = arg[1]
	elif (arg[0]=="-x" or arg[0]=="--prefix"):
		PREFIX = arg[1]
	elif (arg[0]=="-h" or arg[0]=="--help"):
		sintaxi()
		exit()
	arg = arg[2:]

if (len(arg) == 0):
	sintaxi()
	actualParams()

print(C_NONE)

# Establecer el directorio ACTIVITY_DIR como directorio actual
os.chdir(ACTIVITY_DIR)
ACTIVITY_DIR = "."

os.unlink(LOG)

listFiles = os.listdir(ACTIVITY_DIR)
listFiles.sort()

# Busca en el directorio ACTIVITY_DIR los directorios que coincidan con el nombre de la página de proyecto
# Entonces crea un directorio de nombre project y mueve los directorios
# encontrados a este nuevo directorio
# A continuación crea unlaces simbólicos en ACTIVITY_DIR que apuntan a los
# directorios anteriormente movidos
def creaEstructura(page_project):
	global LOG

	# Voltar el directori que és link simbòlic per obtenir tots els seus elements que han de ser eliminats per SFTP
	def voltaLinks(f, ldir):
		linklist = os.listdir(ldir)
		linklist.sort()

		for lfile in linklist:
			actual = ldir+"/"+lfile
			if (os.path.isdir(actual)):
				voltaLinks(f, actual)
				f.write("rmdir " + actual + "\n")
			else:
				f.write("rm " + actual + "\n")

		return

	for file in listFiles:
		if (file > page_project):
			break

		if (file == page_project):
			print("   -pr- "+CB_GRN+ACTUAL_PROJECT+C_NONE)
			print("   -pg- "+CB_GRN+file+C_NONE)
			origin = ACTIVITY_DIR+"/"+file
			new_dir = ACTIVITY_DIR+"/"+PREFIX+ACTUAL_PROJECT+"/"
			destination = new_dir+file
			if (os.path.islink(file)):
				print(CB_CYN+"    origen:["+CB_GRN+origin+CB_CYN+"]"+C_NONE)
				print(CB_CYN+"     destí:["+CB_GRN+destination+CB_CYN+"]"+C_NONE)

				f = open(LOG, "a")
				voltaLinks(f, file)
				f.write("rmdir " + file + "\n")
				f.write("ln -s " + destination + " " + origin + "\n")
				f.close()

	return


# Volta el directori mdprojects cercant projectes.
# Les rutes -transformades- dels projectes son la base per a la
# reorganització dels fitxers exportats dels projectes activityutil
def voltarProjectes(pr_dir):
	global ACTUAL_PROJECT

	def transformDir(dir, glue, **params):
		spl = dir.split("/")
		# valors per defecte
		common_path = MDPROJECTS
		add_prefix = ""
		del_sufix = ""
		for key in params:
			if (key == 'common_path'): common_path = params[key]
			if (key == 'add_prefix'): add_prefix = params[key]
			if (key == 'del_sufix'): del_sufix = params[key]

		nmdp = len([c for c in common_path if c=="/"]) + 1
		#eliminamos del array spl los nmdp primeros elementos que corresponden a la ruta common_path
		#y, en el caso de MDPROJECTS, los 2 elementos finales: el nombre del directorio actual y el del fichero _wikiIocSystem_.mdpr
		spl = spl[nmdp:-2] if (common_path == MDPROJECTS) else spl[nmdp:]
		ret = add_prefix + glue.join(spl)
		return ret.replace(del_sufix, "")

	# Voltar el directori pages cercant les pàgines corresponents al projecte indicat per 'pg_dir'
	def voltaPages(pg_dir):
		print(CB_GRN+"  page: "+C_NONE+pg_dir)
		llista = os.listdir(pg_dir)
		llista.sort()

		for file in llista:
			actual = pg_dir+"/"+file
			if (os.path.isdir(actual)):
				voltaPages(actual)
			elif (actual.endswith(".txt")):
				print (CB_RED+"  actual: "+C_NONE+actual)
				page_project = transformDir(actual, "_", common_path=PAGES, add_prefix=PREFIX, del_sufix=".txt")
				creaEstructura(page_project)

		return

	listProjects = os.listdir(pr_dir)
	listProjects.sort()

	for file in listProjects:
		actual = pr_dir+"/"+file
		if (os.path.isdir(actual)):
			voltarProjectes(actual)
		else:
			if (file == "_wikiIocSystem_.mdpr"):
				ACTUAL_PROJECT = transformDir(actual, "_")
				project_dir = transformDir(actual, "/")
				print(C_NONE+"------------------------------------------------------")
				print(C_NONE+"projecte: "+ACTUAL_PROJECT+" | ruta: "+project_dir)
				print(C_NONE+"------------------------------------------------------")
				project_dir = PAGES+"/"+project_dir
				if (os.path.isdir(project_dir)):
					voltaPages(project_dir)
	return

# ----
# main
# ----
voltarProjectes(MDPROJECTS)
print("=== FI ===")

