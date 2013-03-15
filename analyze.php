<?
	error_reporting(E_ALL);
	ini_set('display_errors', 'On');


	if(isset($_GET['filename'])){
		  
	
		
		$results = shell_exec('python /var/www/thisismattmiller.com/web/citation/extract.py "' . $_GET['filename'] . '" 2>&1');
		

		
		if(@strpos($results,'File "/var/www/thisismattmiller.com/web/citation/extract.py", line')!==false){
		
			//$results =  '{"error" : true }';
			
			$arr = array('error' => true, 'text' => $results);

			$results = json_encode($arr);
		
		}
		
	}

	header('Content-Type: application/json');
	echo $results;
?>