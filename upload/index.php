<?php
/*
 * jQuery File Upload Plugin PHP Example 5.14
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */
 
ini_set('display_errors','On');
ini_set('error_reporting', E_ALL);
error_reporting(E_ALL | E_STRICT);


// Same as error_reporting(E_ALL);


require('UploadHandler.php');
$upload_handler = new UploadHandler();
