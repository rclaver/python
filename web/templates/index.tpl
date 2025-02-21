<!DOCTYPE html>
<html>
<head>
  <meta name="robots" content="index,follow">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>L'apuntador del teatre</title>
  <link rel="icon" type="image/x-icon" href="{{url_for('static', filename='img/favicon.ico')}}">
  <link rel="stylesheet" type="text/css" href="{{url_for('static', filename='css/estils.css')}}" />
  <script src="{{url_for('static', filename='js/script.js')}}"></script>
</head>

<body bgcolor="#FFFFFF">
  <div class="contenidor">
    <div class="titol">L'apuntador del teatre</div>
    <form class="formulari" method="post" action="apuntador">
      <div id="div_seleccio_escenes">
        <legend >Selecció d'escenes {{escena}}</legend>
        <select name="seleccio_escenes" id="seleccio_escenes" size=11>
          <optgroup label="Tot">
            <option value="sencer">obra sencera</option>
          <optgroup label="actors">
            <option value="canut">Canut</option>
            <option value="emma">Emma</option>
            <option value="gisela">Gisela</option>
            <option value="joan">Joan</option>
            <option value="justa">Justa</option>
            <option value="mar">Mar</option>
            <option value="pompeu">Pompeu</option>
            <option value="tina">Tina</option>
        </select>
        <p><input type="submit" value="enviar"></p>
      </div>
    </form>
  </div>
</body>
