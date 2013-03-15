/*
 * jQuery File Upload Plugin JS Example 6.11
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2010, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */

/*jslint nomen: true, unparam: true, regexp: true */
/*global $, window, document */

var cite = {};



$(function () {
    'use strict';
	
	
	
	
	
	
	//The possible catagories to train the system in
	cite.trainCatagories = [
			{"type":"Polarity","options": ['Positive','Negative']}
	]
	cite.trainDataset = [];
	
	
	
	cite.bindAnalyzeButtons = function(){
		$('.btn-analyze').unbind();
		$('.btn-analyze').click(function(event){
			  
			cite.requestAnalysis($(this).data('file'));
			event.preventDefault();
			return false;
	
		});	 		
	}
	
	
	cite.requestAnalysis = function(filename){
		
		
		$('#summaryLink').click();
		$("#summaryLoading").fadeIn();
		$("#summaryStats").fadeOut('fast');
		
		$.ajax({
				url: "analyze.php",
				dataType: 'json',
				data: {'filename' : filename}
			}).done(function (result) {
				
				$("#summaryLoading").fadeOut('fast');
				
				cite.activeFilename = filename;
				
				if (result.hasOwnProperty('error')){
					alert('The python script failed to process this file');	
				}else{
				
					cite.processResults(result);
					
				}
				
				
				
				
		});
		
		
		
	}
	
	
	
	cite.processResults = function(result){
	
		console.log(result);
		$("#summaryStats").fadeIn();
 		$("#summaryStatsCiteCount").text(Object.size(result.data));
		$("#summaryStatsAuthorCount").text(Object.size(result.authors));
		$("#summaryFileName").text(cite.activeFilename);
		
		$("#summaryDocInfo").html("Format: " + result.format + "<br><br>" + "Citation Style: " + result.style + "<br><br>");
		
		cite.trainDataset = [];
		
		cite.buildSummaryDetails(result);
		
		cite.buildLocationMap(result);
		
		cite.trainBuildSentences(result);
		
		cite.cocoBuildNetwork(result);
		
		
	}
	
	
	cite.cocoBuildNetwork = function(result){
	
		var authorLookup = {};
		var edgeLookup = {};
		
		
		var nodes = [];
		var edges = [];
		
		for (var x in result.data){
			
			//only intrested in co-co-ciations
			if (result.data[x].authors.length >= 2){
				
				for (var y in result.data[x].authors){
					var thisAuthor = result.data[x].authors[y];
					
					if 	(!authorLookup.hasOwnProperty(thisAuthor)){
						//add to nodes
						nodes.push({ "name" : thisAuthor });
						authorLookup[thisAuthor] = nodes.length -1;
					}
					
				}
				
				//do it again for the edges
				for (var y in result.data[x].authors){
					
					var author1 = result.data[x].authors[y];
					
					for (var z in result.data[x].authors){
						var author2 = result.data[x].authors[z];
						
						//not themselve
						if (author1 != author2){
							
							
							var relationship = author1 + author2;
							var relationshipInverse = author2 + author1;
							
							if (edgeLookup.hasOwnProperty(relationship) == false && edgeLookup.hasOwnProperty(relationshipInverse) == false){
								
								edges.push({ "source" : authorLookup[author1], "target" : authorLookup[author2], "context" : result.data[x].body + "\n" + result.data[x].note});
								edgeLookup[relationship] = true;
								edgeLookup[relationshipInverse] = true;
								
							}
							//add the realtionship
							
							
						}
						
					}
					
					
				}
				
			}
			
			
			
			
		}
			
	
	
	//build thr network
		
		console.log(nodes,edges);
		
		
		cite.cocoNetwork = {};
	
		cite.cocoNetwork.nodes = nodes;
		cite.cocoNetwork.links = edges;
		
		//Sets up the network force object
		cite.cocoNetwork.init = function(){
			
			
			d3.select("#cocoNetwork svg").remove();
			
			cite.cocoNetwork.tooltip = d3.select("body")
				.append("div")
				.attr('class','d3ToolTip');		
						
			cite.cocoNetwork.width = $("#cocoNetwork").width() - 3;
			cite.cocoNetwork.height = $("#cocoNetwork").height() - 3;
			cite.cocoNetwork.fill = d3.scale.category20();
			
			
			cite.cocoNetwork.vis = d3.select("#cocoNetwork").append("svg")
				.attr("width", cite.cocoNetwork.width)
				.attr("height", cite.cocoNetwork.height)
				.style("fill", "none")
				.call(d3.behavior.zoom() 
	
				  .on("zoom", function() { 
	
					cite.cocoNetwork.vis.attr("transform", "translate(" + d3.event.translate + 
	
					 ")scale(" + d3.event.scale*.7 + ")"); 
				  })); 		
				
			cite.cocoNetwork.vis.append("rect")
				.attr("width", cite.cocoNetwork.width)
				.attr("height", cite.cocoNetwork.height);
				
		
					  
		
			cite.cocoNetwork.vis = cite.cocoNetwork.vis.append("g"); 
		
			cite.cocoNetwork.vis.attr('transform',"scale(" +.7 + ")");
			
			var curve = d3.svg.line()
					  .interpolate("cardinal-closed")
					  .tension(.85);	
	
						
			cite.cocoNetwork.force = d3.layout.force()
				.charge(-1200)
				.gravity(0.2)
				.nodes(cite.cocoNetwork.nodes)
				.distance(100)
				.linkStrength(0.2)
				.theta(1.5)
				.links(cite.cocoNetwork.links)
				.size([cite.cocoNetwork.width, cite.cocoNetwork.height]);			
			
			
				
			
			
			cite.cocoNetwork.force.on("tick", function() {
			 
					
				  cite.cocoNetwork.vis.selectAll(".egoLink")
				  .attr("d", function(d) {
					var dx = d.target.x - d.source.x,
						dy = d.target.y - d.source.y,
						dr = Math.sqrt(dx * dx + dy * dy);
					return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
					});
					
					
				  cite.cocoNetwork.vis.selectAll(".node")
					  .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
				
				 
			});		
			
			
			cite.cocoNetwork.restart();
				
		}
		
		
		
		//starts/restarts the force network layout 
		cite.cocoNetwork.restart = function(){
			
		  
		
		  cite.cocoNetwork.vis.selectAll(".egoLink")
			.data(cite.cocoNetwork.links)
			.enter().append('path')
			  .attr("class", "egoLink")
		  	  .on("mouseover", function(d){ cite.cocoNetwork.tooltip.style("visibility", "visible"); cite.cocoNetwork.tooltip.text(d.context); })
			  .on("mousemove", function(d){return cite.cocoNetwork.tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px");})
			  .on("mouseout", function(d){return cite.cocoNetwork.tooltip.style("visibility", "hidden");})			  
			  .attr("x1", function(d) { return d.source.x; })
			  .attr("y1", function(d) { return d.source.y; })
			  .attr("x2", function(d) { return d.target.x; })
			  .attr("y2", function(d) { return d.target.y; });
		
		  
		  var node = cite.cocoNetwork.vis.selectAll(".node")
			  .data(cite.cocoNetwork.nodes)
			.enter().append("g")
			  .attr("class", "node")
			  .attr("display", function(d) {  'block'})
			  .call(cite.cocoNetwork.force.drag)
			  .on("mouseover", function(d){ cite.cocoNetwork.tooltip.style("visibility", "visible"); cite.cocoNetwork.tooltip.text(d.name); })
			  .on("mousemove", function(d){return cite.cocoNetwork.tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px");})
			  .on("mouseout", function(d){return cite.cocoNetwork.tooltip.style("visibility", "hidden");})
			  .attr("x", function(d, i) { return cite.cocoNetwork.width / 2 + i; })
			  .attr("y", function(d, i) { return cite.cocoNetwork.width / 2 + i; });
			  
			node.append("circle")
				.call(cite.cocoNetwork.force.drag)
				.on("click", function(d){ })
				.style("cursor","pointer")
				.attr("class", function(d){ 
				 
					return "eventNetworkNode";
				
				}) 
	
				.attr("r", function(d) { 
					
					return 15;
					
				
				});  
		
		node.append("rect")
		  .attr("x", function(d) { return -1 * (d.name.length*2.25); })
		  .attr("y", function(d) { return 7; })
		  .attr("height", function(d) { return 10; })
		  .attr("width", function(d) { return (d.name.length*2.25)*2; })
		  .attr("class", "eventNetworkLabelBg")
 	 
		  .style("fill","#fff")
		  .on("click", function(d){ })
		  .style("stroke","#C63F3F");
				
		
				
		node.append("text")
		  .attr("x", function(d) { return 0; })
		  .attr("y", function(d) { return 15; })
		  .attr("class", "eventNetworkLabel")
 			
		  .attr("text-anchor", function(d) { return "middle";})
		
		  .text(function(d) { return d.name; });					  
	
	
			cite.cocoNetwork.force.start();
				
		}	
		
		
		
		
		
		
		cite.cocoNetwork.init ();
		
		
		
	}
	
	cite.buildSummaryDetails = function(result){
		
		
 		$("#summaryCiteDetail, #summaryAuthorDetail").empty();
		
		
		var citations = result.data;
		
		//sort by alpha
		
		
		var citationsAry = [];
		
		for (var aCit in citations){
			citationsAry.push(citations[aCit]);
		}
		
		
		
		
		citationsAry.sort(function(a, b) { 
		
			 
			if (result.style == 'Inline'){
				var textA = a.note.toUpperCase();
				var textB = b.note.toUpperCase();
			}else{
				//if it has the foot/end not number in the beginning 
				
				if (a.note.substr(0,3).match(/\d\d\d|\d\d|\d/) == null){
					var textA = "";
				}else{
					var textA = parseInt(a.note.substr(0,3).match(/\d\d\d|\d\d|\d/)[0]);
				}
				if (b.note.substr(0,3).match(/\d\d\d|\d\d|\d/) == null){
					var textB = "";
				}else{
					var textB = parseInt(b.note.substr(0,3).match(/\d\d\d|\d\d|\d/)[0]);
				}				
  			}
		
			return (textA < textB) ? -1 : (textA > textB) ? 1 : 0;	
 		})
		
		console.log(citationsAry);
		
		//build the details of citations found
		for (var aCit in citationsAry){
			
			$("#summaryCiteDetail").append(
				
				$("<div>")
					.text(citationsAry[aCit].note)
					.addClass('summaryCiteDetailCitation')
					.data('authors', citationsAry[aCit].authors)
					.click(function(){
						
						$(this).children().first().toggle();
						
					})
					.append(
			
						//holds the contect of the citation
						$("<div>")
							.addClass('summaryCiteDetailContext')
							.html(function(){
								
								var returnText = '';
								
								if (result.style == 'Inline'){
									returnText = "Sentence #" + citationsAry[aCit].page;
								}else{
									returnText = "Page #" + citationsAry[aCit].page;
								}
								
								returnText = returnText + "<br>" + citationsAry[aCit].body;
								
								return returnText;
								
							})
					).append(
			
						$("<br>")
					
			
					)
			
			);
			
			
		}
		
		
		var authorsAry = [];
		
		for(var index in result.authors) {
			authorsAry.push({name : index, count : result.authors[index]});
		}
		
		authorsAry.sort(function(a, b) { 
			var textA = a.name.toUpperCase();
			var textB = b.name.toUpperCase(); 
			
			return (textA < textB) ? -1 : (textA > textB) ? 1 : 0;	
		})		
		
		
 		
		for(var index in authorsAry) {
			
 			
			$("#summaryAuthorDetail").append(
				
				$("<div>")
					.text(authorsAry[index].name)
					
					.click(function(){
						
						var searchAuthor = $(this).text();
						
						$("#summaryClearFilter").css("display","inline-block");
 						
						//loop through all the citations
						$(".summaryCiteDetailCitation").each(function(index, element) {
							$(this).fadeIn('fast');
 
						});
						
						$(".summaryCiteDetailCitation").each(function(index, element) {
                            
							
							if (result.style == 'Inline'){
								
								var searchAry = $(this).data("authors");
								
								
								
							}else{
								
								var searchAry = [];
								for (var x in $(this).data("authors")){
									
									//the foot/end style has an array of arrays with [0] = name [1] = bib
									searchAry.push($(this).data("authors")[x][0]);
										 
								}
								
							}
							
							console.log(result.style,searchAry,searchAuthor);
							
							if (searchAry.indexOf(searchAuthor) == -1){
								$(this).fadeOut('fast');	
								
							}
							
							
                        });
						
						
						
						
					}).append(
					
						$("<br>")
						
						
					)
					
			
			
			);
			
			
		}
		 		
		
		$("#summaryClearFilter").css("display","none");
		$("#summaryClearFilter").unbind().click(function(event){
			
			//loop through all the citations
			$(".summaryCiteDetailCitation").each(function(index, element) {
				$(this).fadeIn('fast');

			});
			
			$(this).toggle();
			
			event.preventDefault();
			return false;
		});
		
		
		
		//save for later
		this.citationsAry = citationsAry;
		
		
	}
	
	
	cite.buildLocationMap = function(result){
		
	 
		
		$("#locationTable").empty();
		
		$(".locationLine").each(function(index) {
				
					$(this).remove();
		});
  		
		var authorColor = {};
		var count = 0;
		for(var index in result.authors) {
		
			authorColor[index] = rainbow(Object.size(result.authors),count);
		
			count++;
		
		}
		
		
		var stackTrack = {};
		
	
		for(var index in result.data) {
			
		
			var precentOfDoc = result.data[index].pos / result.docLen * 100;
			
			var mapPercent = 500 * parseFloat(precentOfDoc) / 100;
			
			//console.log(precentOfDoc, mapPercent)
		  
		   
			
			//if there was an error and could not locatate the author still add it with unkown author
			if (result.data[index].hasOwnProperty('authors')){
				var loopAdd = result.data[index];
			}else{
				var loopAdd = result.data[index];
				loopAdd.authors = [['unkown']];
			}
			
			
			//do it differnt ly for foot/end
			if (result.style != "Inline"){
				
				//strip out all the extra stuff (the citation) for the authors array
				
				var newAuthors = []
				for (var aAuthor in loopAdd.authors){
					
					newAuthors.push(loopAdd.authors[aAuthor][0]);
					
					
				}
				
				loopAdd.authors = newAuthors;
				
				
			}
			
			
 		  	for (var aAuthor in loopAdd.authors){
				
				if (loopAdd.authors[aAuthor] == 'unkown'){continue;}
				
				
				if (stackTrack.hasOwnProperty(parseInt(mapPercent) + "px")){
					stackTrack[parseInt(mapPercent) + "px"]  = stackTrack[parseInt(mapPercent) + "px"]  + 1
				}else{
					stackTrack[parseInt(mapPercent) + "px"] = 0;	
				}
				
				
				
				$("#locationMap")
					.append(
						$("<div>")
							.addClass('locationLine')
							.data('author', loopAdd.authors[aAuthor])
							 
							.css("top",parseInt(mapPercent) + "px")
							.append(
							
								$("<div>")
									.addClass('locationPin')
									.attr("title", HtmlEncode(result.data[index].note))
									.css("position","absolute")
									.css("z-index",10000)
									.css("left", function(){
										
										if (stackTrack[parseInt(mapPercent) + "px"] == 0){
											return "";
										}else{
											
											return  (stackTrack[parseInt(mapPercent) + "px"] * 20);
										}
										
									})
									.data('author',function(){ 
									
										return loopAdd.authors[aAuthor];
									
										/*
										if (result.data[index].hasOwnProperty('authors')){
											return result.data[index].authors[0]
										}else{
											return "none";
										}
										*/
									
									})
									.css("background-color", function(){ 
									
										if (loopAdd.authors[aAuthor] == 'unkown'){
											return "#fff";
										}else{
											return authorColor[loopAdd.authors[aAuthor]]
										}
									
										/*
										if (result.data[index].hasOwnProperty('authors')){
											return authorColor[result.data[index].authors[0]]
										}else{
											return "#fff";
										}
										*/
									
									}
									
									)
									
								
								
							)
			   
				
				   );
			}
		}
		
		
		var tuples = [];
		
		for (var key in result.authors) tuples.push([key, result.authors[key]]);
		
		tuples.sort(function(a, b) {
			a = a[1];
			b = b[1];
		
			return a > b ? -1 : (a < b ? 1 : 0);
		});
		
		for (var i = 0; i < tuples.length; i++) {
			var key = tuples[i][0];
			var value = tuples[i][1];
		
			$("#locationTable")
				.append(
					$("<tr>")
						.data("author",key)
						.append(
							$("<td>")
								.text(i+1)
						)					
						.append(
							$("<td>")
								.text(key)
						)
						.append(
							$("<td>")
								.text(value)
						)
					.mouseenter(function(event){
				
						console.log($(this));	
						var lookFor = $(this).data('author');
						
						
						
						$(".locationLine").each(function(index) {
  							
							if($(this).data('author') == lookFor){
								
								$(this).css('visibility','visible');
								
							}else{
								$(this).css('visibility','hidden');
							}
							
							
                        });
						
					
					}).mouseleave(function(event){
				
				
						
						$(".locationLine").each(function(index) {
                            
						
								$(this).css('visibility','visible');
							
							
							
                       });})	
																
				)
		
		
			
			// do something with key and value
		}		
		
		
		
	}
	
	
	
	//builds the interface to build a training set based on the configured catagories for training
	cite.trainBuildSentences = function(result){
		
	
		var useSentences = [];
  		
		//add in unique sentences
		for (var x in result.data){
	
			var body = result.data[x].body;
			var note = result.data[x].note;
			
			body = body.replace('-\n','');
			body = body.replace('\n',' ');
			note = note.replace('-\n','');
			note = note.replace('\n',' ');
			
			//if it is a foot or end note also include the note text along with the context of the occurance
			if (result.style=='Footnotes' || result.style=='Endnotes'){
			
				useSentences.push(body + '<br><br>' + "---NOTE---" + "<br><br>" + note);
					
				
			}else{

		
				if (useSentences.indexOf(body) == -1){
					useSentences.push(body);
				}				
				
			}
			
			
		}
		 
	
		//store
		cite.trainSentences = useSentences;
		
		//build the interface
		$("#trainSentenceHolder").empty();
		 
		for (var i = 0; i < useSentences.length; i++) {
			
			var useColor = i % 2 === 0 ? "#E1E1E1" : "white";
			
			var trainOptions = $("<div>");
			 
			
			for (var aCat in cite.trainCatagories){
				
				var useCat = $("<div>")
					.addClass("catOptionHolder")
					.append(
						$("<div>")
							.addClass("trainCatHolder")
							.append($("<span>").text(cite.trainCatagories[aCat].type))
							
							.append(
								$("<button>")
									.text(cite.trainCatagories[aCat].options[0])
									.addClass('btn') 
									.addClass('btn-mini')
									.addClass('btn-success')
									.data("type",cite.trainCatagories[aCat].type)
									.data("option",cite.trainCatagories[aCat].options[0])
									.click(function(event){cite.trainGetTextSelected($(this));})	
							).append(
								$("<button>")
									.text(cite.trainCatagories[aCat].options[1])
									.addClass('btn')
									.addClass('btn-mini')
									.addClass('btn-danger')
									.data("type",cite.trainCatagories[aCat].type)
									.data("option",cite.trainCatagories[aCat].options[1])									 
									.click(function(event){cite.trainGetTextSelected($(this));})										
							).append(
								$("<button>")
									.text("Test")
									.addClass('btn')
									.addClass('btn-mini')
									.addClass('btn-info')
									.button()
									.data("type",cite.trainCatagories[aCat].type)
									.data("option",cite.trainCatagories[aCat].options[1])									 
									.click(function(event){
										
										var testText = '';
										
										//grab the parent dom
										testText = $(this).parentsUntil( $("#trainSentenceHolder"))[3];
										//grab that text (first child) remove ---NOTE--- if there (for foot/end note style)
										testText = $(testText).children().first().text().replace("---NOTE---","");
										$(this).button('loading');
										
										var theButton = $(this);
										
										$.get('classify.php?test=' + testText,function(data){
												
												theButton.button('reset');
												
												console.log(data);
												
												var text = "Results: " + data.results + "  Pos: " +  data.positive + "  Neg: " +  data.negative;
 												theButton.text(text);
												
												//$(this).append($("<span>").text(text));
 												
												
										})
										.error(function() { alert('Internal Server Error'); });											 
										
									})										
							)
							
							
							
					).append($("<br>").addClass("clearfix")).append($("<br>").addClass("clearfix"));
				
				trainOptions.append(useCat);
				
				
				
			}
			
			
			//add each items with the text to use and the options to train with
			$("#trainSentenceHolder").append(
				$("<div>")
					.attr("id","trainASetence" + i)
					.addClass("trainSetences")
					.css("background-color",useColor)
					.css("padding","5px")
					.append(
						$("<h5>")
							.html(useSentences[i])
					)
					.append(trainOptions)
					
					
					
			);
		
			
			
		}
		
		
		
		//add the buttons to submit
		$("#trainSentenceHolder")
			.append(
				$("<hr>")
			)
		
			.append(
				$("<button>")
					.addClass("btn")
					.attr("id","trainSetButton")
					.addClass("btn-primary")
					.text("Submit Training Set")
					.button()
					.click(function(){
						
						$(this).button('loading');
						
						
						//send 
						cite.trainTrainSet();
						
						
						
					})
		);
		
		
		
	}
	
	
	cite.trainTrainSet = function(){
	
		$.post('classify.php',{train : cite.trainDataset}, function(data) {
  			 
			 $(".removeTrainData").text("This rule hass been added!").attr("disabled", true).css("width","auto");
			 
			 $("#trainSetButton").button('reset');
			 
			 $("#trainSetButton").text('Training Set submitted!');
 
		}).error(function() { alert('Internal Server Error'); });;			
	
	}
	
	//get the text selected and add it to the data set for that classifyer type and option
	cite.trainGetTextSelected = function(domObj){
		
			
		
		if (typeof window.getSelection != "undefined") {
			
			var selObj = window.getSelection(); 
			
			var text = 	selObj.toString().trim();
			
			if (text==''){return false}
			
			//clear	
			if ( document.selection ) {
				document.selection.empty();
			} else if ( window.getSelection ) {
				window.getSelection().removeAllRanges();
			}		
			
			
			//add a remove option to the controls
			domObj.parent().append(
				
				$("<div>")
					.append(
						$("<span>")
						.css("color","#666")
						.text(domObj.data("option") + ": " + text)
					)
					.append(
						$("<button>")
							.addClass("btn")
							.addClass("btn-mini")
							.addClass("removeTrainData")
							.data("text",text)
							.data("option",domObj.data("option"))
							.css("width","20px")
							.css("height","20px")
							.css("margin-left","5px")
							.text("X")
							.attr("title","remove")
							.click(function(){
							
								$(this).parent().remove();
								
								
								//cycle through the added items to the dataset and remove
								//also remove the item from the controls
								for (var x in cite.trainDataset){
									
									if (cite.trainDataset[x].option ==  $(this).data("option") && cite.trainDataset[x].text == $(this).data("text") ){
										
										cite.trainDataset.splice(x,1);
										 
										 return
									}
									
									
								}
							}
							)
					)	
			
			);
			
			//add more space below the control
			domObj.parent().parent().append($("<br>").addClass("clearfix"));
			 
			
			//add it to the training set
			cite.trainDataset.push(
				
				{
					"type" : 	domObj.data("type").toLowerCase(),
					"option" : domObj.data("option").toLowerCase(),
					"text" : text.trim()  
					
				}
			
			
			)
			
 		
		}
		
	}	
	
	
	
	
	
	
	
	
	
	$('#myTab a').click(function (e) {
		e.preventDefault();
		$(this).tab('show');
	})
	
	
 
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	//some upload library stuff
	
	

    // Initialize the jQuery File Upload widget:
    $('#fileupload').fileupload({
        url: 'upload/',
		autoUpload: true
    })
	.bind('fileuploadalways', function (e, data) {
		
		
		setTimeout(function() {
		  cite.bindAnalyzeButtons()
		}, 500);  // will work with every browser	
		
	});

    // Enable iframe cross-domain access via redirect option:
    $('#fileupload').fileupload(
        'option',
        'redirect',
        window.location.href.replace(
            /\/[^\/]*$/,
            '/cors/result.html?%s'
        )
    );



	// Load existing files:
	$.ajax({
		// Uncomment the following to send cross-domain cookies:
		//xhrFields: {withCredentials: true},
		url: $('#fileupload').fileupload('option', 'url'),
		dataType: 'json',
		context: $('#fileupload')[0]
	}).done(function (result) {
		if (result && result.length) {
			$(this).fileupload('option', 'done').call(this, null, {result: result});
			cite.bindAnalyzeButtons();
		}
	});


	
	Object.size = function(obj) {
		var size = 0, key;
		for (key in obj) {
			if (obj.hasOwnProperty(key)) size++;
		}
		return size;
	};

	
	function HtmlEncode(s)
	{
	  var el = document.createElement("div");
	  el.innerText = el.textContent = s;
	  s = el.innerHTML;
	  return s;
	}
	 

	function rainbow(numOfSteps, step) {
		// This function generates vibrant, "evenly spaced" colours (i.e. no clustering). This is ideal for creating easily distiguishable vibrant markers in Google Maps and other apps.
		// Adam Cole, 2011-Sept-14
		// HSV to RBG adapted from: http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript
		var r, g, b;
		var h = step / numOfSteps;
		var i = ~~(h * 6);
		var f = h * 6 - i;
		var q = 1 - f;
		switch(i % 6){
			case 0: r = 1, g = f, b = 0; break;
			case 1: r = q, g = 1, b = 0; break;
			case 2: r = 0, g = 1, b = f; break;
			case 3: r = 0, g = q, b = 1; break;
			case 4: r = f, g = 0, b = 1; break;
			case 5: r = 1, g = 0, b = q; break;
		}
		var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
		return (c);
	}	
 

});


