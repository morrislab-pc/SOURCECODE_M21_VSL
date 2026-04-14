#Mult1: visual statistical learning, center, no-task
scenario = "VSL_triggers_2023.sce";
default_background_color = 255,255,255;
active_buttons = 4;
button_codes = 1,2,3,4;
response_matching = simple_matching; 
response_logging = log_active;
stimulus_properties = block, string, triplet, string, p_code, number, object, string;
event_code_delimiter = "/";
default_output_port = 1;
write_codes = true; 
pulse_out= false;
pulse_width = 3; 


begin;

array{
bitmap { filename = "inst1.jpg"; description = "inst1"; } inst1;
bitmap { filename = "break.jpg"; description = "break"; } break;
bitmap { filename = "inst2.jpg"; description = "inst2"; } inst2;
bitmap { filename = "inst3.jpg"; description = "inst3"; } inst3;
bitmap { filename = "question.jpg"; description = "question"; } question;
bitmap { filename = "pause.jpg"; description = "pause"; } pause;
bitmap { filename = "end.jpg"; description = "end"; } end;
} instructions;

array{
   bitmap { filename = "t1.jpg"; description = "1"; } A;
   bitmap { filename = "t2.jpg"; description = "2"; };
   bitmap { filename = "t3.jpg"; description = "3"; } ;
   bitmap { filename = "t4.jpg"; description = "4"; } ;
   bitmap { filename = "t5.jpg"; description = "5"; } ;
   bitmap { filename = "t6.jpg"; description = "6"; } ;
   bitmap { filename = "t7.jpg"; description = "7"; } ;
   bitmap { filename = "t8.jpg"; description = "8"; } ;
   bitmap { filename = "t9.jpg"; description = "9"; } ;
   bitmap { filename = "t10.jpg"; description = "10"; } ;
   bitmap { filename = "t11.jpg"; description = "11"; } ;
   bitmap { filename = "t12.jpg"; description = "12"; } ;
   bitmap { filename = "t13.jpg"; description = "13"; } ;
   bitmap { filename = "t14.jpg"; description = "14"; } ;
   bitmap { filename = "t15.jpg"; description = "15"; } ;
   bitmap { filename = "t16.jpg"; description = "16"; } ;
   bitmap { filename = "t17.jpg"; description = "17"; } ;
   bitmap { filename = "t18.jpg"; description = "18"; } ;
   bitmap { filename = "t19.jpg"; description = "19"; } ;
   bitmap { filename = "t20.jpg"; description = "20"; } ;
   bitmap { filename = "t21.jpg"; description = "21"; } ;
   bitmap { filename = "t22.jpg"; description = "22"; } ;
   bitmap { filename = "t23.jpg"; description = "23"; } ;
   bitmap { filename = "t24.jpg"; description = "24"; } ;
}objects;
 
#part 1
#instructions
trial {
   trial_duration = forever;
   trial_type = first_response;
      stimulus_event {
      picture {
         bitmap inst1;
         x = 0; y = 0;
      }pic1;
      code = "inst1";
}event1;
}instrcut1_trial;

trial {
   trial_duration = forever;
   trial_type = specific_response;
    terminator_button = 3;
      stimulus_event {
      picture {
         bitmap break;
         x = 0; y = 0;
      }pic2;
      code = "break";
}event2;
}break_trial;

#triplet
trial {
   trial_duration = 1000;
    stimulus_event {
      picture {
         bitmap A;
         x = 0; y = 0;
      }pic3;
duration = 800; 
code = "object";
response_active=true;
}event3;
}main_trial;

#part 2
#instrcutions
trial {
   trial_duration = forever;
   trial_type = first_response;
      stimulus_event {
      picture {
         bitmap inst2;
         x = 0; y = 0;
      }pic4;
      code = "inst3";
		}event4;
		}instrcut2_trial;
		
trial {
   trial_duration = forever;
   trial_type = first_response;
      stimulus_event {
      picture {
         bitmap inst3;
         x = 0; y = 0;
      }pic5;
      code = "inst3";
		}event5;
		}instrcut3_trial;

#test trial
trial {
	trial_duration = 1000;
	stimulus_event {
	picture {
	bitmap A;
	x = 0; y = 0;
	}pic6;
	code = "test";
	duration = 800; 
   }event6;
    }test_trial;
   
   #question
	trial {
   trial_duration = forever;
   trial_type = first_response;
    terminator_button = 4;
      stimulus_event {
      picture {
         bitmap question;
         x = 0; y = 0;
      }pic7;
	code = "question";
	}event7;
	}question_trial;

#pause
trial {
   trial_duration = 1000;
      stimulus_event {
      picture {
         bitmap pause;
         x = 0; y = 0;
      }pic8;
code = "pause";
}event8;
}pause_trial;

#end
trial {
   trial_duration = forever;
   trial_type = specific_response;
    terminator_button = 3;
      stimulus_event {
      picture {
         bitmap end;
         x = 0; y = 0;
      }pic9;
	}event9;
	}end_trial;

	
# ----------------------------PCL----------------------------------

begin_pcl;

array<int>objlist[0];
loop int index = 1 until index> objects.count() begin 
	string file_names = objects[index].description(); 
	int filenameint = int(file_names);
	objlist.add(filenameint); 
	index = index+1
end; 

objects.shuffle();

#create an output file
output_file out = new output_file;
out.open_append(logfile.subject() +"_results.txt");
out.print ("part1 ");

#creating triplets array
int triplet_count = 8;
int triplet_size = 3;

array<bitmap>triplets[triplet_count][triplet_size];
loop int i = 1; int index = 1 until i > triplet_count begin
   loop int j = 1 until j > triplet_size
   begin
      triplets[i][j] = objects[index];
      index = index + 1;
      j = j + 1;
   end;
   i = i + 1;
end;

instrcut1_trial.present();

#repeat of triplets
array<int>which_triplet[triplets.count()];
which_triplet.fill( 1, 0, 1, 1 );
int num_reps = 24; #24

#no 2 triplets in a row
loop int i = 1; int last = 0; until i > num_reps begin
loop which_triplet.shuffle() until which_triplet[1] != last begin which_triplet.shuffle(); end;

loop int l = 1 until l > which_triplet.count() begin
		loop int j = 1 until j > triplet_size begin
		pic3.set_part(1, triplets[which_triplet[l]][j]);
		event3.set_event_code(triplets[which_triplet[l]][j].description() + ";" + string(which_triplet[l]));
		event3.set_port_code(10*i+which_triplet[l]);
		main_trial.present();
      j = j + 1;
		end;
		out.print(which_triplet[l]);
		out.print(" ");
	last = which_triplet[which_triplet.count()];
	l = l + 1;
	end;
    i = i + 1;
end;

main_trial.present();

break_trial.present();

#creating foils
array<bitmap>foil1[3];
foil1[1]=(triplets[1][1]);
foil1[2]=(triplets[2][2]);
foil1[3]=(triplets[3][3]);

array<bitmap>foil2[3];
foil2[1]=(triplets[2][1]);
foil2[2]=(triplets[3][2]);
foil2[3]=(triplets[4][3]);

array<bitmap>foil3[3];
foil3[1]=(triplets[3][1]);
foil3[2]=(triplets[4][2]);
foil3[3]=(triplets[1][3]);

array<bitmap>foil4[3];
foil4[1]=(triplets[4][1]);
foil4[2]=(triplets[1][2]);
foil4[3]=(triplets[2][3]);

array<bitmap>foil5[3];
foil5[1]=(triplets[5][1]);
foil5[2]=(triplets[6][2]);
foil5[3]=(triplets[7][3]);

array<bitmap>foil6[3];
foil6[1]=(triplets[6][1]);
foil6[2]=(triplets[7][2]);
foil6[3]=(triplets[8][3]);

array<bitmap>foil7[3];
foil7[1]=(triplets[7][1]);
foil7[2]=(triplets[8][2]);
foil7[3]=(triplets[5][3]);

array<bitmap>foil8[3];
foil8[1]=(triplets[8][1]);
foil8[2]=(triplets[5][2]);
foil8[3]=(triplets[6][3]);

array<bitmap>foils[8][3];
foils[1]=(foil1);
foils[2]=(foil2);
foils[3]=(foil3);
foils[4]=(foil4);
foils[5]=(foil5);
foils[6]=(foil6);
foils[7]=(foil7);
foils[8]=(foil8);

array<bitmap>stims[2][8][0];
stims[1].assign(triplets);
stims[2].assign(foils);

#combinations of triplets and foils 	
array<int>combo[32][2] = { {1,1}, {1,2}, {1,3}, {1,4}, {2,1}, {2,2}, {2,3}, {2,4}, {3,1}, {3,2}, {3,3}, {3,4}, {4,1}, {4,2}, {4,3}, {4,4}, {5,5}, {5,6}, {5,7}, {5,8}, {6,5}, {6,6}, {6,7}, {6,8}, {7,5}, {7,6}, {7,7}, {7,8}, {8,5}, {8,6}, {8,7}, {8,8} };
combo.shuffle();

#counterbalancing order of triplet and foil
array<int>which_first[32];
which_first.fill( 1, 16, 1, 0 );
which_first.fill( 17, 32, 2, 0 );
which_first.shuffle();

instrcut2_trial.present();
instrcut3_trial.present();
out.print ("part2 ");

loop int i = 1 until i > combo.count() begin
	array<int>order[2] = {1,2};
	if which_first[i] == 2 then
	order = {2,1};
	end;

loop int k = 1 until k > 2 begin
	loop int j = 1 until j > triplet_size begin
		pic6.set_part( 1, stims[order[k]][combo[i][order[k]]][j] );
		event6.set_event_code( stims[order[k]][combo[i][order[k]]][j].description() + ";" + string(combo[i][order[k]]) + ";" + string(order[k]));
		event6.set_port_code((100*which_first[i])+i);
		test_trial.present();
		j = j + 1;
	end;
	out.print(combo[i][order[k]]);
	out.print(" ");
	pause_trial.present();
k = k + 1;
end;
	out.print(which_first[i]);
	out.print(" ");
question_trial.present(); 
		if (which_first[i] == 1 ) && (response_manager.last_response()==1) then out.print ("1 "); 
		elseif (which_first[i] == 1 ) && (response_manager.last_response()==2) then out.print ("2 ");
		elseif (which_first[i] == 2 ) && (response_manager.last_response()==1) then out.print ("2 "); 
		elseif (which_first[i] == 2 ) && (response_manager.last_response()==2) then out.print ("1 "); end;
		i = i + 1;
end;
end_trial.present();
