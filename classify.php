<?
	error_reporting(E_ALL);
	ini_set('display_errors', 'On');


	if(isset($_POST['train'])){
		  
 		foreach ($_POST['train'] as $trainObj){
			
			
			$trainObj['type'] = htmlspecialchars($trainObj['type']); 
			$trainObj['option'] = htmlspecialchars($trainObj['option']); 
			$trainObj['text'] = htmlspecialchars($trainObj['text']); 
 			
			
			$string = $trainObj['text'] . "\n";
			
			//write to the training file
			if ($trainObj['option'] == 'positive'){
				
				//first test if this is a dupe
				if (file_exists('positive.csv')){
					$allFile = file_get_contents('positive.csv');
					if (strpos($allFile,$string) !== false){
						$string = '';	
					}
				}
				
				file_put_contents('positive.csv',$string,FILE_APPEND);
			}else if($trainObj['option'] == 'negative'){
				
				//first test if this is a dupe
				if (file_exists('negative.csv')){
					$allFile = file_get_contents('negative.csv');
					if (strpos($allFile,$string) !== false){
						$string = '';	
					}
				}
								
				file_put_contents('negative.csv',$string,FILE_APPEND);
			}
			
		}
		
		$results = '{ "results" : true }';
		
		
	}else if(isset($_GET['test'])){
		
		
		$aug1 = "analyze";
		$aug2 = escapeshellarg($_GET['test']);
		
		$results = shell_exec('python /var/www/thisismattmiller.com/web/citation/classify.py ' . $aug1 . ' ' . $aug2 . ' 2>&1');
  		
		
	}else if(isset($_GET['features'])){
		
		
		$aug1 = "features";
		$aug2 = escapeshellarg($_GET['features']);
		
		$results = shell_exec('python /var/www/thisismattmiller.com/web/citation/classify.py ' . $aug1 . ' ' . $aug2 . ' 2>&1');
  		
		
	}else if(isset($_GET['positive'])){
		
		header('Content-Type: text/plain');
		echo file_get_contents('positive.csv');
		
		die();
	}else if(isset($_GET['negative'])){
		
		header('Content-Type: text/plain');
		echo file_get_contents('negative.csv');
		
		die();
	}

	header('Content-Type: application/json');
	echo $results;
?>