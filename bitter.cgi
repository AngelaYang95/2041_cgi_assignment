#!/usr/bin/perl -w

# Written Angela Yang September 2015
# Bitter social platform assignment for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/


use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Data::Dumper;
use List::Util qw/min max/;
use POSIX qw(strftime);

main();

sub main {

    # show warnings in HTML
    warningsToBrowser(1);

    # some globals used through the script
    $debug = 1;
    $dataset_size = "medium";
    $users_dir = "dataset-$dataset_size/users";
    $bleats_dir = "dataset-$dataset_size/bleats";
	#pagination for n = 10
	$page_size = 10;

    populate_variables();

    #only allow use if logged in.
    if(validate_login()) {
		print page_header();
		my $username = $variable_list{'logged_in_user'};
		my $password = $variable_list{'logged_in_password'};
		my $nav_status = $variable_list{'nav_status'};
		my $back_path = "$users_dir/$username/background.jpg";


		if(-e $back_path) {
			print custom_background($back_path);
		}
		print rant_form();
		print nots_form();

		#setup tweet
		if(defined param("tweet")) {
			# append to files
			add_new_tweet();
		}
		if(defined param('action')) {
			if ($variable_list{'action'} eq "remove_background") {
				remove_pic('background')
			} elsif($variable_list{'action'} eq "remove_profile_pic") {
				remove_pic('profile');
			} elsif ($variable_list{'action'} eq "change_nots") {
				change_nots();
			} elsif ($variable_list{'action'} eq "picture") {
				change_profile_pic();
			} elsif ($variable_list{'action'} eq "background") {
				change_background_pic();
			} elsif ($variable_list{'action'} eq "change_details") {
				change_details();
			} elsif ($variable_list{'action'} eq "delete") {
				#remove tweet from user's list and from bleats dir.
				delete_tweet();
			} elsif($variable_list{'action'} eq "listen") {

				#add in listener to list
				my $tweet_id = new_subscription();
			} else {
				#delete user listener from list
				end_subscription();
			}
		}
		print basic_form($username, $password, $nav_status);
        print nav_bar();

        print browse_screen();
    } else {
		print basic_header();
		print basic_nav();
		if(defined param('action')) {
			if($variable_list{'action'} eq "recover_password") {
				send_password();
			} elsif($variable_list{'action'} eq "suspend_account") {
				suspend_account();
			} elsif($variable_list{'action'} eq "delete_account") {
				delete_account();
			} elsif($variable_list{'action'} ne "create_account") {
				send_confirmation_email();
			}
		}
		if(defined param('action') && $variable_list{'action'} eq "create_account") {

			print custom_body();
			print create_account_form();
		} else {
			print custom_body();
		    print login_screen();
			print "</body>";
		}
    }
	print java_scripts();
    print page_trailer();
}

sub custom_background {
	my $file = $_[0];
	return<<eof;
<body style="background: url($file) no-repeat center center fixed;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;">
eof
}

sub suspend_account() {
	my $username = param("user_profile") || die "username of account to suspend not given";
	my $dest = "$users_dir/suspended_accounts.txt";

	open my $f, ">>$dest";
	print $f "$username\n";
	close $f;
	print<<eof;
<div class="row" style="background-color:#ffffff; margin:4em; text-align:center;">
Your account $username has been suspended.
Sign in to unsuspend.
</div>
eof
}

sub remove_pic {
	my $type = $_[0];
	my $path_to_remove = "$users_dir/$variable_list{'logged_in_user'}/$type.jpg";
	unlink $path_to_remove if -e $path_to_remove;
}


sub delete_account {
	my $user = param('user_profile') || die "USERNAME NOT CARRIED ON IN DELETING";
	# delete their bleats from bleats dir.
	my $user_bleats = fetch_users_bleats($user);
	my @bleat_list = split(' ',$user_bleats);
	foreach my $id(@bleat_list) {
		chomp $id;
		my $bleat_path = "$bleats_dir/$id";
		unlink $bleat_path if -e $bleat_path;
	}

	my $profile_dir = "$users_dir/$user";
	unlink $profile_dir if -e $profile_dir;
}

# if currently on, then
sub change_nots {
	my $token = "$users_dir/$variable_list{'logged_in_user'}/notification";
	if(-e $token) {
		unlink $token;
	} else {
		open my $f, ">$token";
		print $f "notify by email";
		close $f;
	}
}

sub change_background_pic {
	my $new_photo = param("photo") || die "problem with image upload line change_background_pic()";
	if($new_photo ne "0") {
		my $photo_path = "$users_dir/$variable_list{'logged_in_user'}/background.jpg";
		open (IMAGE_FILE, ">$photo_path") or die "problem opening photo imge $!";
		binmode IMAGE_FILE;

		while ( <$new_photo> ) {
			print IMAGE_FILE;
		}
		close IMAGE_FILE;
	}
}

sub change_profile_pic {

	#Basic input sanitisation
	my $new_photo = param("photo") || die "problem with image upload line change_profile_pic()";
	if($new_photo ne '0') {
		open (IMAGE_FILE, ">$users_dir/$variable_list{'logged_in_user'}/profile.jpg" ) or die "problem opening photo imge $!";
		binmode IMAGE_FILE;

		while ( <$new_photo> ) {
			print IMAGE_FILE;
		}
		close IMAGE_FILE;
	}
}

#Email the user who has just created an account
sub send_confirmation_email {
	print h2('sending confirmation email');
	my $username = "$variable_list{'logged_in_user'}";
	my $email_body = <<eof;
<h1>Welcome to Bitter!</h1>
<br>
<pre>
		You have signed up as user $username
		<a href="#">Click here to confirm you accout</a>
</pre>
eof
}

sub send_password() {
	my $username = param("username") || "ERROR VARIABLE";
	my $path = "$users_dir/$username/details.txt";
	if(-e $path) {
		open my $f, "$path" or die "couldn't open $path";
		my $details = join(' ',<$f>);
		close $f;

		my ($email2) = $details =~ /email: (.+)/;
		my ($password) = $details =~ /password: (.+)/;
		my $email = 'angela.yang95@gmail.com';
		my $message =<<eof;
		Password Recovery

		Hi $username,

		Below is your recovered password
		Password: $password
eof

		print print <<eof;
<div class="row" style="background-color:#ffffff;margin:4em; text-align:center;">
Your password was sent to $email2</div>;
eof
	} else {
		print <<eof;
<div class="row" style="background-color:#ffffff;margin:4em; text-align:center;">
The username $username doesn't exist</div>;
eof
	}
}

sub change_details {
	my $path = "$users_dir/$variable_list{'logged_in_user'}/details.txt";
	open my $in, "<$path" or die "couldn't open $path, $!";
	my @contents = <$in>;
	close $in;

	open my $out,">$path" or die "couldn't open $path, $!";
	my $about_defined = 0;
	my $home_defined = 0;
	foreach my $line(@contents) {
		chomp $line;
		my ($key, $value) = split(': ',$line);

		if(defined param($key) ) {
			print $out "$key: $variable_list{$key}\n";
		} else {
			print $out "$key: $value\n";
		}
		if($key eq "about") {
			$about_defined = 1;
		} elsif($key eq "home_suburb") {
			$home_defined = 1;
		}
	}

	# for those not yet defined in details.txt file
	if(!$about_defined) {
		print $out "about: ";
		if(defined param('about')) {
			my $about = param('about');
			print $out "$about";
		}
		print $out "\n";
	}

	if(!$home_defined) {
		print $out "home_suburb: ";
		if(defined param('home_suburb')) {
			my $home = param('home_suburb');
			print $out "$home";
		}
		print $out "\n";
	}
	close $out;

}

sub custom_body {
	return<<eof;
<body style="background: url(http://bwalles.com/wp-content/uploads/2013/10/Rainy-Day-1080p-Background-18-.jpg) no-repeat center center fixed;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;">
eof
}

sub create_account_form {

	return<<eof;
<body>
<div style="height:75%; padding-left:21em; padding-right: 21em; padding-top: 3em;">
<form class="form-horizontal" style="padding:3em; border-radius: 1em; background-color:#ffffff;">
  <fieldset>
    <legend>Join Bitter</legend>

    <div class="form-group">
      <label for="inputEmail" class="col-lg-2 control-label">Username</label>
      <div class="col-lg-10">
        <input type="text" class="form-control" id="inputUsername" placeholder="Username (required)">
      </div>
    </div>

    <div class="form-group">
      <label for="inputPassword" class="col-lg-2 control-label">Password</label>
      <div class="col-lg-10">
        <input type="password" class="form-control" id="inputPassword" placeholder="Password (required)">
      </div>
    </div>

    <div class="form-group">
      <label for="inputEmail" class="col-lg-2 control-label">Email</label>
      <div class="col-lg-10">
        <input type="text" class="form-control" id="inputEmail" placeholder="Email (required)">
      </div>
    </div>

    <div class="form-group">
      <label for="textArea" class="col-lg-2 control-label">About Me</label>
      <div class="col-lg-10">
        <textarea class="form-control" rows="3" id="textArea"></textarea>
        <span class="help-block">A longer block of help text that breaks onto a new line and may extend beyond one line.</span>
      </div>
    </div>

	<div class="form-group">
      <label for="inputSuburb" class="col-lg-2 control-label">Suburb</label>
      <div class="col-lg-10">
        <input type="text" class="form-control" id="inputSuburb" placeholder="Suburb">
      </div>
    </div>


    <div class="form-group">
      <label class="col-lg-2 control-label"></label>
      <div class="col-lg-10">
        <div class="radio">
          <label>
            <input type="radio" name="optionsRadios" id="optionsRadios1" value="option1" checked="">
            Send notifications to my email
          </label>
        </div>
        <div class="radio">
          <label>
            <input type="radio" name="optionsRadios" id="optionsRadios2" value="option2">
            Turn off notifications
          </label>
        </div>
      </div>
    </div>

    <div class="form-group">
      <div class="col-lg-10 col-lg-offset-2">
        <button type="reset" class="btn btn-default">Clear Form</button>
        <button type="submit" class="btn btn-primary">Submit</button>
      </div>
    </div>

  </fieldset>
</form>
</div>
</body>
eof
}

sub basic_nav {

return<<eof;
<nav class="navbar navbar-default">
  <div class="container-fluid">
    <div class="navbar-header">
      </button>
      <a class="navbar-brand" href="rant.cgi">Bitter</a>
    </div>
  </div>
</nav>
eof
}

#delete a tweet based on ID
sub delete_tweet() {
	my $tweet_id = $variable_list{'tweet_id'} || print h1("error tweet_id not passed on");
	my $tweet_path = "$bleats_dir/$tweet_id";

	open my $f, $tweet_path or die "couldn't open $tweet_path\n";
	my ($username) = join('',<$f>) =~ /username: ?(.*)/;

	my $user_path = "$users_dir/$username/bleats.txt";

	open IN, "<$user_path" or die "couldn't open $user_path";
	my @id_list = <IN>;
	close IN;

	@id_list = grep !/$tweet_id/, @id_list;

	open OUT, ">$user_path" or die "couldn't open $user_path";
	print OUT @id_list;
	close OUT;
	unlink $tweet_path if -e $tweet_path;
}


sub add_new_tweet {
	my $epoc = time();

	#getting tweet id
	my @id_list = glob("$bleats_dir/*");
	my $temp = join(' ', @id_list);
	$temp =~ s/$bleats_dir\///g;
	@id_list = split(' ',$temp);
	my @sorted_id_list = sort @id_list;
	@sorted_id_list = reverse @sorted_id_list;

	my $tweet_id = $sorted_id_list[0];
	$tweet_id++;
	my $type = "";
	my $original_user = "";
	if (defined param('tweet_id')) {
		$type ="in_reply_to: $variable_list{'tweet_id'}";
		open my $f, "$bleats_dir/$variable_list{'tweet_id'}" or die "couldn't open the original tweet reply is for $!";
		my $origin = join(' ',<$f>);
		($original_user) = $origin =~/username: (.+)/;
		chomp $original_user;
		$original_user = " \@$original_user";

	}
		#creating tweet file:
		my $file_text = <<eof;
time: $epoc
longitude:
latitiude:
bleat:$original_user $variable_list{"tweet"}
username: $variable_list{"logged_in_user"}
$type

eof

	# Create a new tweet file
	open my $g, ">./$bleats_dir/$tweet_id" || die "\nUnable to create $tweet_id\n";
	print $g "$file_text";
	close $g;

	#add bleat id to bleats.txt file
	my $user_tweet_path = "$users_dir/$variable_list{'logged_in_user'}/bleats.txt";
	open my $f, ">>$user_tweet_path" || die "Unable to open $user_tweet_path\n";
	print $f "$tweet_id\n";
	close $f;

	return $tweet_id;
}

sub new_subscription {
	my $detail_path = "$users_dir/$variable_list{'logged_in_user'}/details.txt";

	open my $g, "$detail_path" or die "cannot open user file";
	my $detail_text = join ' ', <$g>;
	$detail_text =~ s/listens:/listens: $variable_list{'listen_to'}/;
	close $g;

	open my $f, ">$detail_path" or die "cannot open user file";
	print $f "$detail_text";
	close $f;
}

sub end_subscription {
	my $detail_path = "$users_dir/$variable_list{'logged_in_user'}/details.txt";

	open my $g, "$detail_path" or die "cannot open user file";
	my $detail_text = join ' ', <$g>;
	$detail_text =~ s/$variable_list{'listen_to'}//;
	close $g;

	open my $f, ">$detail_path" or die "cannot open user file";
	print $f "$detail_text";
	close $f;
}

#updates variables with parameter values
sub populate_variables {
	$variable_list{"password"} = param("password") if defined param("password");
	$variable_list{"home_suburb"} = param("home_suburb") if defined param("home_suburb");
	$variable_list{"full_name"} = param("full_name") if defined param("full_name");
	$variable_list{"about"} = param("about") if defined param("about");

	$variable_list{"tweet"} = param("tweet") if defined param("tweet");
	$variable_list{"action"} = param("action") if defined param("action");
	$variable_list{"listen_to"} = param("listen_to") if defined param("listen_to");
	$variable_list{"tweet_id"} = param("tweet_id") if defined param("tweet_id");
    $variable_list{"nav_status"} = param("nav_status") || 0;
    $variable_list{"keyword"} = param("keyword") || "No Results Found";
    $variable_list{"user_profile"} = param("user_profile") || "";
    $variable_list{"logged_in_user"} = param("logged_in_user") || 0;
    $variable_list{"logged_in_password"} = param("logged_in_password") || 0;

}

#--------------------------------------------------------------------
#						FORM MAKING SUB ROUTINES
#
#--------------------------------------------------------------------

sub rant_form {
		my $rant_form = '<form method="POST" id="rant_form">';
	foreach my $parameter (keys %variable_list) {
		my $value = $variable_list{$parameter};
		$rant_form .= "<input type='hidden' form='rant_form' name='$parameter' value='$value'>\n" if $parameter ne "tweet";
	}
	$rant_form .= "</form>";
	return $rant_form;
}

sub nots_form {
	my $rant_form = '<form method="POST" id="nots_form">';
	foreach my $parameter (keys %variable_list) {
		my $value = $variable_list{$parameter};
		$rant_form .= "<input type='hidden' form='nots_form' name='$parameter' value='$value'>\n" if $parameter ne "action" && $parameter ne "tweet";
	}
	$rant_form .= "<input type='hidden' name='action' value='change_nots' form='nots_form'></form>";
	return $rant_form;
}

sub basic_form {
	my $username = $_[0];
	my $password = $_[1];
	my $nav_status = $_[2];

	return <<eof;
	<form id="basic_form" method="POST">
	<input type="hidden" name="logged_in_user" value="$username" form="basic_form">
	<input type="hidden" name="logged_in_password" value="$password" form="basic_form">
	<input type="hidden" name="nav_status" id="nav_status" value="$nav_status" form="basic_form">
	</form>
eof
}

#-------------------------------
#header for the login page only
sub basic_header {

	return <<eof;
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Bitter |Rant</title>
	<link href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.5/flatly/bootstrap.min.css" rel="stylesheet">
	<script src="//code.jquery.com/jquery-1.11.3.min.js"></script>
	<script src="//code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
	<script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
    <!--script src="js/vendor/modernizr.js"></script-->
  </head>
eof
}


sub page_header {
	return <<eof
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Bitter |Rant</title>
	<link href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.5/flatly/bootstrap.min.css" rel="stylesheet">
	<link rel="stylesheet" href="css/foundation.css"/>
	<script src="//code.jquery.com/jquery-1.11.3.min.js"></script>
	<script src="//code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
	<script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
  </head>
eof
}


# HTML placed at bottom of every screen
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

#check if username and password are correct
sub validate_login {
    my $username = $variable_list{"logged_in_user"} || 0;
    my $password = $variable_list{"logged_in_password"} || 0;

    if($username && $password) {
		my $user_path = "$users_dir/$username/details.txt";
        if (-e $user_path) {
            open my $p, "$user_path" or die "cannot open user file";
            my $details = join ' ',<$p>;
            if ($details =~ /password: $password\b/) {
				#make sure it's not on suspend list
				unsuspend_account();
				$variable_list{"nav_status"} = "home" if !defined param("nav_status");
				param("nav_status","home") if !defined param("nav_status");
                return 1;
            }
        }
    }
    return 0;
}

#-------------------------------
# Unsuspends teh logged in user if they had a suspended account
#-------------------------------
sub unsuspend_account() {
	my $username = $variable_list{'logged_in_user'};
	my @contents;
	open my $in, "<$users_dir/suspended_accounts.txt";
	@contents = <$in>;
	close $in;

	open my $out, ">$users_dir/suspended_accounts.txt";
	foreach my $line(@contents) {
		print $out "$line" if $line !~ /$username/;
	}
	close $out;
}

#-------------------------------
# gives the login page
# or form for account creation
#-------------------------------
sub login_screen {
    my $username = $variable_list{"logged_in_user"};
    my $password = $variable_list{"logged_in_password"};
    my $user = "";
	my $pass = "";

    if(!$username && !$password) {
        $user =<<eof;
        <input type="text" placeholder="username" name="logged_in_user" class="form-control" id="user-box">
eof
		$pass=<<eof;
        <input type="password" placeholder="password" name="logged_in_password" class="form-control" id="pass-box">
eof
    } elsif(!$password) {
        $user =<<eof;
        <input type="text" value="$username" name="logged_in_user" class="form-control" id="user-box">
eof
		$pass=<<eof;
        <input type="password" placeholder="password" name="logged_in_password" class="form-control" id="pass-box">
        Please provide your password
eof
    } elsif(!$username) {
        $user =<<eof;
        <input type="text" placeholder="username" name="logged_in_user" class="form-control" id="user-box">
        Please provide your username
eof
		$pass =<<eof;
        ><input type="password" placeholder="password" name="logged_in_password" class="form-control" id="pass-box">
eof
    } else { #they've given a username and password
        my $user_path = "$users_dir/$username/details.txt";
        if (!-e $user_path) {
            $user =<<eof;
            <input type="text" placeholder="username" name="logged_in_user" class="form-control" id="user-box">
			invalid username
eof
			$pass =<<eof;
            <input type="password" placeholder="password" name="logged_in_password" class="form-control" id="pass-box">
eof
        } else {
            $user =<<eof;
<input type="text" value="$username" name="logged_in_user" class="form-control" id="user-box">
eof
			$pass =<<eof;
            <input type="password" placeholder="password" name="logged_in_password" class="form-control" id="pass-box">
            <br> incorrect password
eof
        }
    }
    return login_template($user, $pass);
}

#-------------------------------
# template design for the landing page
# Takes in login form as parameter
# Login template taken from http://bootsnipp.com/snippets/3qMPD
#-------------------------------
sub login_template {
    my $user = $_[0];
	my $pass = $_[1];
    return<<eof
<div class="container" style="margin-top: 4em;">

	<!-- START MODAL -->
	<div id="recover_password" class="modal fade" role="dialog">
		  <div class="modal-dialog"  style="margin-top: 20em;">

			<!-- Modal content-->
			<div class="modal-content">
				  <div class="modal-header">
					<button type="button" class="close" data-dismiss="modal">&times;</button>
					<h4 class="modal-title">Password Recovery Form</h4>
				  </div>

				  <div class="modal-body">
					<!--div class="col-lg-10"-->
						<h7>Your password will be sent to your email address</h7>
						<!--div class="form-group"-->

						<form method="POST" id="recovery_form">
								<input type="hidden" name="action" value="recover_password"  form="recovery_form">
								<label for="textArea">Username</label>
								<input type="text" maxlength="20" rows="3" id="username" name="username" form="recovery_form" placeholder="Username">
						</form>
						<!--/div-->
					<!--/div-->
				  </div>


				  <div class="modal-footer">
					<button type="submit" class="btn btn-primary" form="recovery_form">Submit</button>
					<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
				  </div>
			</div>

		  </div>
	</div>
	<!-- END MODAL-->


    <div class="row">
        <div class="col-md-4 col-md-offset-7" style="margin-left:25em;">

            <div class="panel panel-default" style="opacity: 0.9;">
                <div class="panel-heading">
                    <span class="glyphicon glyphicon-lock"></span> Login</div>
                <div class="panel-body">
                    <form method="POST" id="login" class="form-horizontal" role="form">
                    <div class="form-group">
                        <label for="user-box" class="col-sm-3 control-label">
                            Username</label>
                        <div class="col-sm-9">
                            $user
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="pass-box" class="col-sm-3 control-label">
                            Password</label>
                        <div class="col-sm-9">
                            $pass
                        </div>
                    </div>
                    <div class="form-group last">
                        <div class="col-sm-offset-3 col-sm-9">
                            <button type="submit" class="btn btn-success btn-sm" form="login">
                                Sign in</button>
                                <button type="reset" class="btn btn-default btn-sm">
                                Reset</button>
                        </div>
                    </div>
					<!--input type="hidden" name="nav_status" value="home" id="nav_status" form="login"-->
                    </form>
					<span class="help-block"><a data-toggle="modal" href="#recover_password">Recover Password</a></span>
                </div>
                <div class="panel-footer">
					<form method="POST" id="create_account" role="form">
						<input type="hidden" name="action" value="create_account" id="action" form="create_account">
					</form>
                    Not Registred? <a onclick="document.getElementById('create_account').submit(); return false;" href="javascript:void(0);"> Click Here to Register</a>
				</div>
            </div>
        </div>
    </div>
</div>
eof
}

#-------------------------------
# Gets bleats relevant to logged in user for the home screen
#-------------------------------
sub get_bleats {
	my $current_user = $variable_list{"logged_in_user"};
	my $username = "";
	my $time = "";
	my $unique_id = "";
	my $bleat_html = "";

	# CHECK IF THIS NEEDS TO BE SORTED
	my $total_bleats = 0;
	my $page_num = param('page_num') || '1';
	my $end = $page_size*$page_num;
	my $start = $end - 10;
	foreach my $tweet_file (reverse(sort(glob("$bleats_dir/*")))) {
		open (my $f, $tweet_file);
		my $detail = join(' ', <$f>);

		if($detail =~/$current_user/) {
			$total_bleats++;
			next if $total_bleats <= $start || $total_bleats > $end;
			($bleat) = $detail =~ /bleat: ?(.*)/;
			chomp $bleat;
			($username) = $detail =~ /username: ?(.*)/;
			chomp $username;
			($epoch) = $detail =~ /time: ?(.*)/;
			chomp $epoch;
			$tweet_file =~ s/$bleats_dir\///;
			my $time = convert_time($epoch);
			#$home_tweet_list{$time}{$username} = $bleat;
			$bleat_html .= tweet_widget($bleat,$username,$tweet_file, $time);
		}
	}
	my $pagers = create_pagination($total_bleats);
	return <<eof;
$bleat_html
	<ul class="inline-list">
				$pagers
		 </ul>
    </div>
eof
}


#-------------------------------
# Directs which page is displayed based on the nav_status
#-------------------------------
sub browse_screen {
    if ($variable_list{"nav_status"} eq "home") {
        return home_screen();
    } elsif ($variable_list{"nav_status"} eq "search") {
		#my $keyword = $variable_list{"keyword"};
        return search_user();
    } elsif ($variable_list{"nav_status"} eq "search_tweet") {
		return search_tweets();
	} elsif ($variable_list{"nav_status"} eq "profile") {
        return show_profile();
    } elsif($variable_list{"nav_status"} eq "edit_profile") {
		return profile_editor();
	} elsif ($variable_list{"nav_status"} eq "view_responses" || defined param('tweet_id')) {
		return view_responses();
	}
    return h1("ERROR IN PAGE REDIRECTION"), h4("$variable_list{'nav_status'}");
}

#-----------------------------------------
# FORM FOR EDITING PROFILE. no params
#-----------------------------------------
sub profile_editor {
	my $path = "$users_dir/$variable_list{'logged_in_user'}/details.txt";
	my $line = "";

	open my $f, "$path" or die "Couldn't open $path";
	my $details = join(' ',<$f>);
	close $f;

	my $about ="";
	($about) = $details =~ /about: (.*)/ if $details =~ /about:/;
	my $suburb = "";
	($suburb) = $details =~ /home_suburb: (.*)/ if $details =~ /home_suburb:/;
	my $full_name = "";
	($full_name) = $details =~ /full_name: (.*)/ if $details =~ /full_name:/;
	my $password = "";
	($password) = $details =~ /password: (.*)/ if $details =~ /password:/;
	my $username = "";
	($username) = $details =~ /username: (.*)/ if $details =~ /username:/;
	my $notify ="";
	if(-e "$users_dir/$variable_list{'logged_in_user'}/notify") {
		$notify = <<eof;
eof
	} else {
				$notify = <<eof;
eof
	}

	return<<eof;
<!--UPLOAD IMAGE MODAL-->
<div class="modal" id="change_profile">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h4 class="modal-title">Change Profile Image</h4>
      </div>
      <div class="modal-body">
        <p>Upload Jpeg</p>
		<form method="POST" id="picture" enctype="multipart/form-data">
			<input type="hidden" name="logged_in_user" value="$variable_list{'logged_in_user'}" form="picture">
			<input type="hidden" name="logged_in_password" value="$variable_list{'logged_in_password'}" form="picture">
			<input type="hidden" name="nav_status" id="nav_status" value="$variable_list{'nav_status'}" form="picture">
			<input type="hidden" name="action" value="picture">
			<input type="file" name="photo" value="0">
		</form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="submit" class="btn btn-primary" form="picture">Upload</button>
      </div>
    </div>
  </div>
</div>

<!--CHANGE BACKGROUND-->
<div class="modal" id="change_background">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h4 class="modal-title">New Background Image</h4>
      </div>
      <div class="modal-body">
        <p>Upload Jpeg</p>
		<form method="POST" id="background" enctype="multipart/form-data">
			<input type="hidden" name="logged_in_user" value="$variable_list{'logged_in_user'}" form="background">
			<input type="hidden" name="logged_in_password" value="$variable_list{'logged_in_password'}" form="background">
			<input type="hidden" name="nav_status" id="nav_status" value="$variable_list{'nav_status'}" form="background">
			<input type="file" name="photo" form="background" value="0">
		</form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="submit" class="btn btn-primary" form="background" name="action" value="background">Upload</button>
      </div>
    </div>
  </div>
</div>

<!--REMOVE IMAGE-->
<div class="modal" id="remove_image">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
        <h4 class="modal-title">New Background Image</h4>
      </div>
      <div class="modal-body">
        <p>Which image would you like to <b>delete</b>?</p>
		<form method="POST" id="remove_pic">
			<input type="hidden" name="logged_in_user" value="$variable_list{'logged_in_user'}" form="remove_pic">
			<input type="hidden" name="logged_in_password" value="$variable_list{'logged_in_password'}" form="remove_pic">
			<input type="hidden" name="nav_status" id="nav_status" value="$variable_list{'nav_status'}" form="remove_pic">
			<button type="submit" class="btn btn-primary" form="remove_pic" name="action" value="remove_background">Background</button>
			<button type="submit" class="btn btn-primary" form="remove_pic" name="action" value="remove_profile_pic">Profile Picture</button>
		</form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>

<div class="list-group" style="margin-right:18em;margin-left:18em;margin-top:5em;">
	<div class="list-group-item active">
	Edit Profile
	</div>

	<div href="#" class="list-group-item">
	<!--START FORM-->
	<form method="POST" id="details" class="form-horizontal">
		  <fieldset>
			<legend>Profile Details</legend>

			<div class="form-group">
			  <label for="inputUsername" class="col-lg-2 control-label">Username</label>
			  <div class="col-lg-10">
				<input type="text" class="form-control" id="inputUsername" name="username" value="$username">
			  </div>
			</div>

			<div class="form-group">
			  <label for="inputFullname" class="col-lg-2 control-label">Fullname</label>
			  <div class="col-lg-10">
				<input type="text" class="form-control" id="inputFullname" name="full_name" value="$full_name">
			  </div>
			</div>

			<div class="form-group">
			  <label for="inputSuburb" class="col-lg-2 control-label">Suburb</label>
			  <div class="col-lg-10">
				<input type="text" class="form-control" id="inputSuburb" name="home_suburb" value="$suburb">
			  </div>
			</div>

			<div class="form-group">
			  <label for="inputPassword" class="col-lg-2 control-label">Change Password</label>
			  <div class="col-lg-10">
				<input type="text" class="form-control" id="inputPassword" name="password" value="$password">
			  </div>
			</div>

			<div class="form-group">
			  <label for="textArea" class="col-lg-2 control-label">About Me</label>
			  <div class="col-lg-10">
				<textarea class="form-control" rows="3" id="textArea" name="about" form="details" maxlength="200">$about</textarea>
				<span class="help-block">max. 200 characters</span>
			  </div>
			</div>

			<div class="form-group">
			  <div class="col-lg-10 col-lg-offset-2">
				<input type="hidden" name="logged_in_user" value="$variable_list{'logged_in_user'}" form="details">
				<input type="hidden" name="logged_in_password" value="$variable_list{'logged_in_password'}" form="details">
				<input type="hidden" name="nav_status" id="nav_status" value="$variable_list{'nav_status'}" form="details">
				<input type="hidden" name="action" value="change_details">
				<button type=submit class="btn btn-default" form="basic_form">Cancel</button>
				<button type="submit" class="btn btn-primary" form="details">Submit</button>
			  </div>
			</div>
		  </fieldset>
	</form>
	<!-- END FORM -->

  </div>
  <a data-toggle="modal" href="#change_profile" class="list-group-item"><span class="glyphicon glyphicon-picture"></span> Upload New Profile Picture
  </a>
  <a data-toggle="modal" href="#change_background" class="list-group-item"><span class="glyphicon glyphicon-picture"></span> Upload New Background Image
  </a>
  <a data-toggle="modal" href="#remove_image" class="list-group-item">Remove Profile/Background Image
  </a>
</div>

<!--div class="list-group" style="margin: 6em;"-->
	$notify
<!--/div-->

eof
}

#-------------------------------
#return screen with tweets that contains this sub string
#-------------------------------
sub search_tweets() {
	my $keyword = $variable_list{"keyword"};

	my $tweet_list_html = "";
	my $total_bleats = 0;
	my $page_num = param('page_num') || '1';
	my $end = $page_size*$page_num;
	my $start = $end - 10;
	foreach my $file_path (reverse sort glob("$bleats_dir/*")) {
		open my $f, "<$file_path" or die "couldn't open $file_path";
		my $detail = join(' ', <$f>);
		if($detail =~ /bleat:.*$keyword/i) {
			$total_bleats++;
			next if $total_bleats <= $start || $total_bleats > $end;
			my ($id) = $file_path =~ /$bleats_dir\/(.*)/;
			my ($tweet) = $detail =~ /bleat: ?(.*)/;
			my ($username) = $detail =~ /username: ?(.*)/;
			my ($epoch) = $detail =~ /time: ?(.+)/;
			my $time = convert_time($epoch);
			$tweet_list_html .= tweet_widget($tweet,$username,$id, $time);
		}
		close $f;
	}
	my $pagers = create_pagination($total_bleats);
	$tweet_list_html =~ s?$keyword?<b>$keyword</b>?g;
	$tweet_list_html = "<hr/>".$tweet_list_html if $tweet_list_html ne "";
	return<<eof;
<div class="alert alert-dismissible alert-info" style="text-align:center; border-radius:0px; margin-bottom: 1px">
  <h3 style="color:#FFFFFF">$keyword</h3>
</div>
<div class="large-3 columns">
	<div class="panel">
	</div>
</div>

<div class="large-6 columns" style="background-color:#E6E6E6">
	$tweet_list_html
	$pagers
</div>

eof
}


#-------------------------------
# Displays all responses to the original tweet. Will give a list with the
# original tweet right at the top
# param: original tweet
#-------------------------------
sub view_responses {
	my $original_tweet = $variable_list{'tweet_id'};
	# collect in a hash
	# response_list{bleat_id}{dataname}{value}
	%response_list = ();
	%original = ();
	foreach my $path (reverse sort glob("$bleats_dir/*")) {
			open my $f, $path or die "couldn't open $path\n";
			$path =~ s?$bleats_dir/??;

			my $detail = join ('&', <$f>);
			if($detail =~ /in_reply_to: $original_tweet/) {

				my @lines = split('&', $detail);
				foreach my $line(@lines) {
					chomp $line;
					my($key,$value) = split(': ', $line);
					$response_list{"$path"}{"$key"} = $value;
				}
			} elsif($path =~ /$original_tweet/) {
				my @lines = split('&', $detail);
				foreach my $line(@lines) {
					chomp $line;
					my($key,$value) = split(': ', $line);
					$original{"$key"} = $value;
				}
			}
			close $f;
	}

	my $original_html = "";
	my $o_time = convert_time($original{'time'});
	$original_html = tweet_widget($original{'bleat'},$original{'username'},$original_tweet,$o_time) if -e "$bleats_dir/$original_tweet";
	my $state = "Responses";
	my $html ="";
	if(%response_list) {

		foreach my $key (keys %response_list) {
			my $r_time = convert_time($response_list{$key}{'time'});
			$html .= tweet_widget($response_list{$key}{'bleat'},$response_list{$key}{'username'},$key,$r_time);
		}
	} else {
		$state = "No Responses";
	}

	return<<eof;
<div class="alert alert-dismissible alert-info" style="text-align:center; border-radius:0px;">
  <h3 style="color:#FFFFFF">$state</h3>
</div>
<div style="background-color:#E6E6E6"><hr/>
	$original_html
</div>

<div class="large-6 columns" style="background-color:#ffffff; margin-left:25em;"><hr/>
	$html
</div>

eof
}

#-------------------------------
# Searches for all users with the keystring as substring of
# full name or username
# Will not show any suspended accounts
# param: keyword
#-------------------------------
sub search_user {
	my $keyword = param("keyword");
	my @user_list = sort(glob("$users_dir/*"));
	open my $s, "$users_dir/suspended_accounts.txt";
	my $suspended_accounts = join('',<$s>);
	close $s;


	my $total_bleats = 0;
	my $page_num = param('page_num') || '1';
	my $end = $page_size*$page_num;
	my $start = $end - 10;
	foreach my $username(@user_list) {

		open my $p, "$username/details.txt";
		my @list = <$p>;
		close $p;
		$username =~ s?^.*users\/??g;
		if($suspended_accounts =~ /$username/i || $username =~ /suspended_accounts.txt/) {
			next;
		}
		if($username =~ /$keyword/i || $keyword eq "" || join('',@list) =~/full_name: $keyword/i) {
			$total_bleats++;
			next if $total_bleats <= $start || $total_bleats > $end;
			foreach my $line(@list) {
				chomp $line;
				my ($key, $value) = split(': ',$line);
				$bleat_account_details{$username}{$key} = $value;
			}
		}
		close $p;
	}
	my $pagers = create_pagination($total_bleats);

	my $html ="<div class='container'>";
	my $count = 1;
	foreach my $username (sort keys %bleat_account_details) {
		$html.="<div class='row'>" if $count % 2 == 0;
		$html.=user_widget_template($username);
		$html.="</div>" if $count % 2 == 0;
		$count++;
	}
	$html .="</div>";
	$keyword = "All Users" if $keyword eq "";
	return <<eof;
<div class="alert alert-dismissible alert-info" style="text-align:center; border-radius:0px; margin-bottom: 1em">
  <h3 style="color:#FFFFFF">$keyword</h3>
</div>
<!--hr/-->
$html
<div class="large-6 columns" style="margin-left:20em;">
	<ul class="inline-list">
	$pagers
	</ul>
</div>
      <footer class="row">
        <div class="large-12 columns">
          <hr/>
          <div class="row">
            <div class="large-5 columns">
              <p>© Bitter</p>
            </div>
            <div class="large-7 columns">

            </div>
          </div>
        </div>
      </footer>
eof
}

# nav_bar helper function
sub save_login {
	my $username = $variable_list{"logged_in_user"};
	my $password = $variable_list{"logged_in_password"};
	return<<eof
    	<input type="hidden" name="logged_in_user" value="$username">
	<input type="hidden" name="logged_in_password" value="$password">
eof
}

#--------------------------
#	Navigation bar template
#-------------------------------
sub nav_bar {
	my $save_login = save_login();
	my $user = $variable_list{'logged_in_user'};
	my $user_profile = param('user_profile') || "AaronSurfer264";
	my $page = param('page_num') || '0';
	my $nots = "Turn On Notifications";
	if(-e "$users_dir/$variable_list{'logged_in_user'}/notification") {
		$nots = "Turn Off Notifications"
	}

    return<<eof;
	<!-- Modal -->
	<div id="account_modal" class="modal fade" role="dialog">
	  <div class="modal-dialog">

		<!-- Modal content-->
		<div class="modal-content">
			  <div class="modal-header">
				<button type="button" class="close" data-dismiss="modal">&times;</button>
				<h4 class="modal-title">Remove Account</h4>
			  </div>

			  <div class="modal-body">
				<div class="col-lg-10">
				<div class="form-group">
					<button type ="submit" class="btn btn-primary" name="action" value="suspend_account" form="account_suspend">Suspend Account</button>
					<button type ="submit" class="btn btn-primary" name="action" value="delete_account" form="account_suspend">Delete Account</button>
					<form method="POST" id="account_suspend">
							<input type="hidden" name="user_profile" value="$variable_list{'logged_in_user'}" form="account_suspend">
					</form>
					</div>
				</div>
			  </div>


			  <div class="modal-footer">
				<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
			  </div>
		</div>
	</div>
	</div>

	<!-- RANT FORM Modal -->
	<div id="rant_modal" class="modal fade" role="dialog">
	  <div class="modal-dialog">

		<!-- Modal content-->
		<div class="modal-content">
			  <div class="modal-header">
				<button type="button" class="close" data-dismiss="modal">&times;</button>
				<h4 class="modal-title">SEND BLEAT</h4>
			  </div>

			  <div class="modal-body" style="height:9em;">
				<div class="col-lg-10">
				<div class="form-group">
					<textarea type="text" class="form-control" style="width:25em;" maxlength="142" rows="4" id="textArea" name="tweet" form="rant_form" placeholder="max. 142 characters"></textarea>
				</div>
				</div>
			  </div>


			  <div class="modal-footer" style="heigh:3em; padding: 1em;">
				<ul class="inline-list" style="float:right;">
					<li><button type="submit" class="btn btn-primary" form="rant_form">Bleat</button></li>
					<li><button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button></li>
				</ul>
			  </div>
		</div>
	  </div>
	</div>

    <!--start bootstrap template-->
<nav class="navbar navbar-default" style="border-radius: 2px; margin-bottom: 1px;">
  <div class="container-fluid">
    <div class="navbar-header">

	<!--ONLY FOR SHRUNK WINDOWS-->

	    <a class="navbar-brand" onclick="document.getElementById('nav_status').value='home'; document.getElementById('basic_form').submit();return false;" href="javascript:void(0);">
			Bitter <span class="glyphicon glyphicon-home"></span>
		</a>
    </div>

    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
      <ul class="nav navbar-nav">
        <li><a onclick="give_profile_search('$user')"  href="javascript:void(0);">
			Profile
		</a></li>
      	</ul>
	 <form class="navbar-form navbar-left" role="search" id="search_form" method="POST">
        <div class="form-group">
           <input type="text" class="form-control" placeholder="Search" form="search_form" name="keyword">
    		</div>
		$save_login
        <button type="submit" class="btn btn-default" name="nav_status" value="search" form="search_form">
			<span class="glyphicon glyphicon-user"></span>
			User
		</button>
		<!--drop down menu-->
		<button type="submit" class="btn btn-default" name="nav_status" value="search_tweet" form="search_form">
			<span class="glyphicon glyphicon-search"></span>
			Bleat
		</button>
	</form>
      <ul class="nav navbar-nav navbar-right">
		<li><a href="#rant_modal" data-toggle="modal"><span class="glyphicon glyphicon-pencil"></span></a></li>
		 <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false"><span class="glyphicon glyphicon-cog"><span class="caret"></span></a>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#account_modal" data-toggle="modal">Edit Account</a></li>
			<li><a onclick="change_nots()" href="javascript:void(0);">$nots</a></li>
            <li class="divider"></li>
            <li><a onclick="edit_profile()" href="javascript:void(0);">Edit Profile</a></li>
          </ul>
        </li>
        <li><a href="?">
			Logout
		</a></li>
      </ul>
    </div>
  </div>
</nav>
eof
}

#-------------------------------
# checks if logged in user is subscribed to this account
# param: username
#-------------------------------
sub is_subscribed {
	my $user_to_check = $_[0];
	open $f, "$users_dir/$variable_list{'logged_in_user'}/details.txt";
	my $details = join(' ', <$f>);

	if($details =~ $user_to_check) {
		return 1;
	}
	return 0;
}

#-------------------------------
# HTML template for displaying tweets.
# param: tweet content. username. bleat id and time
#-------------------------------
sub tweet_widget {
	my $bleat = $_[0];
	my $username = $_[1];
	my $profile_image = "$users_dir/$username/profile.jpg";
	my $bleat_id = $_[2];
	my $time = $_[3];

	if(!-e $profile_image) {
		$profile_image = "http://placehold.it/80x80&text=[img]";
	}

	my $logged_in_user = $variable_list{"logged_in_user"} || "ERROR";
	my $nav_status = $variable_list{"nav_status" } || "ERROR";
	my $password = $variable_list{"logged_in_password"} || "ERROR";
	my $delete_button = "";
	my $page_num = param('page_num') || -1;
	if($username =~ /$logged_in_user/) {
		$delete_button =<<eof;
	<button type="button" class="btn btn-default btn-sm" onclick="delete_tweet($bleat_id,'$username',$page_num)">			<!--if it's a string, it needs to be quoted. if scalar it doesn't-->
          <span class="glyphicon glyphicon-trash"></span> Delete
    </button>
eof
	}
	return<<eof;
          <div class="row">
            <div class="large-2 columns small-3"><img src="$profile_image"></div>
            <div class="large-10 columns">
              <p><a onclick="give_profile_search('$username')" href="javascript:void(0);"><strong>$username</a></strong>  <medium style="color:#808080">$time</medium>
			 <br>$bleat</p>
              <ul class="inline-list">
                <li>
					<a data-toggle="modal" href="#myModal">Reply</a>
				</li>
				 <li>
					<a id="responses" href="javascript:void(0);" onclick="view_responses($bleat_id)">View Responses</a>
				 </li>
				<li style="float:right;">
					$delete_button
				</li>
              </ul>
					<!-- Modal -->
					<div id="myModal" class="modal fade" role="dialog">
					  <div class="modal-dialog">

						<!-- Modal content-->
						<div class="modal-content">
							  <div class="modal-header">
								<button type="button" class="close" data-dismiss="modal">&times;</button>
								<h4 class="modal-title">Reply to bleat</h4>
							  </div>

							  <div class="modal-body">
								<label for="textArea" class="col-lg-2 control-label">Reply</label>
		  						<div class="col-lg-10">
								<div class="form-group">

									<form method="POST" id="reply_form">
											<input type="hidden" name="logged_in_user" value="$variable_list{'logged_in_user'}" form="reply_form">
											<input type="hidden" name="logged_in_password" value="$variable_list{'logged_in_password'}" form="reply_form">
											<input type="hidden" name="nav_status" id="nav_status" value="$variable_list{'nav_status'}" form="reply_form">
											<input type="hidden" name="user_profile" id="user_profile" value="$variable_list{'user_profile'}" form="reply_form">
											<input type="hidden" name="tweet_id" id="tweet_id" value="$bleat_id" form="reply_form">
											<input type="hidden" name="keyword" id="keyword" value="$variable_list{'keyword'}"  form="reply_form">
											<textarea class="form-control" maxlength="142" rows="3" id="textArea" name="tweet" form="reply_form" placeholder="max. 142 characters"></textarea>
									</form>
								</div>
								</div>
							  </div>


							  <div class="modal-footer">
								<button type ="submit" class="btn btn-primary" form="reply_form"><span class="glyphicon glyphicon-pencil"></span></button>
								<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
							  </div>
						</div>

					  </div>
					</div>

			</div>
		</div>

        <hr/>
eof
}

#-------------------------------
# fetches all the bleats id's which belong to the user
# param: username of the account you want the bleats of
#-------------------------------
sub fetch_users_bleats{
	my $user_to_show = $_[0];
	my $bleat_file = "$users_dir/$user_to_show/bleats.txt";
	open my $f, "$bleat_file" or die "cannot open $bleat_file";
	my $users_bleats = join(' ',<$f>);

	close $f;
	return $users_bleats;

eof
}

#-----------------------------------
# CALCULATES PAGINATION REQUIREMENTS
# param: number of bleats which satisfy results altogether
#-----------------------------------
sub create_pagination {
	my $total_bleats = $_[0];
	my $pagers = "";
	my $num = "0";
	my $user = $variable_list{'user_profile'} || "";			#die "ISSUE WAS HERE with user_profile $!";
	my $key = param('keyword') || "";

	if(defined param('page_num')) {
		$num = param('page_num');
		if ($num > 1) {
			$pagers = <<eof;
<li><a href="javascript:void(0);" onclick="get_page($num-1,'$user','$key')">Newer</a></li>
eof
		}
	} else {
		$num = 1;
	}

	my $dir_size = $total_bleats;
	if($page_size*$num < $dir_size) {
		$pagers.=<<eof;
<li style="float:right"><a onclick="get_page($num+1,'$user','$key')" href="javascript:void(0);">Older</a></li>
eof
	}
	return $pagers;
}

sub convert_time {
	my $epoch_time = $_[0];
	my $converted_time = "";

	$converted_time = strftime("%m.%d.%Y",localtime($epoch_time));
	return $converted_time;
}

#-------------------------------------------
# GIVES HTML PROFILE PAGE
# profile specified by param('user_profile')
#-------------------------------------------
sub show_profile {
    my $user_to_show = param("user_profile");
    my $details_filename = "$users_dir/$user_to_show/details.txt";
    my $picture_path = "$users_dir/$user_to_show/profile.jpg";

	if(!-e $picture_path) {
		$picture_path = "http://placehold.it/300x440&text=[ad]";
	}

    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    my $profile = join '', <$p>;
    close $p;

    my ($full_name) = $profile =~ /full_name: ?(.*)/;
    my ($listens_to) = $profile =~ /listens: ?(.*)/;
	my @user_accounts = split(' ',$listens_to);
	$listens_to ="";
	foreach my $account(@user_accounts) {
		$listens_to .= <<eof;
	<a onclick="give_profile_search('$account')" href="javascript:void(0);">$account</a><br>
eof
	}

    my $home_suburb = "Unknown";
	($home_suburb) = $profile =~ /home_suburb: ?(.*)/ if $profile =~ /home_suburb: .+/;
	my $about = "";
	($about) = $profile =~ /about: ?(.*)/ if $profile =~ /about: .+/;

	my $username = $variable_list{"logged_in_user"};
	my $password = $variable_list{"logged_in_password"};
	my $nav_status = $variable_list{"nav_status"};

	my $listen_button_html = "";

	#check if user is subscribed to this
	# subscription
	if($user_to_show ne $username) 	{
		if(!is_subscribed($user_to_show)) {
			$listen_button_html = <<eof;
<form method="POST" id="listen_form">
<input type="hidden" name="logged_in_user" value="$username" form="listen_form">
<input type="hidden" name="logged_in_password" value="$password" form="listen_form">
<input type="hidden" name="nav_status" id="nav_status" value="$nav_status" form="listen_form">
<input type="hidden" name="listen_to" value="$user_to_show" form="listen_form">
<input type="hidden" name="user_profile" value="$user_to_show" form="listen_form">
<button type='submit' form='listen_form' name='action' value='listen'>Listen</button>
</form>
eof
		} else {
			$listen_button_html = <<eof;
<form method="POST" id="listen_form">
<input type="hidden" name="logged_in_user" value="$username" form="listen_form">
<input type="hidden" name="logged_in_password" value="$password" form="listen_form">
<input type="hidden" name="nav_status" id="nav_status" value="$nav_status" form="listen_form">
<input type="hidden" name="listen_to" value="$user_to_show" form="listen_form">
<input type="hidden" name="user_profile" value="$user_to_show" form="listen_form">
<button type='submit' form='listen_form' name='action' value='Unlisten'>Unlisten</button>
eof
		}
	}

	# GRAB PAGINATION
	# Gets the id of all the belats from this user
	my $users_bleats = fetch_users_bleats($user_to_show);
	my $tweet_html = "";
	my $total_bleats = 0;
	my $page_num = param('page_num') || '1';
	my $end = $page_size*$page_num;
	my $start = $end - 10;
	foreach my $id_path (reverse sort(glob("$bleats_dir/*"))) {
		my ($id) = $id_path =~ /$bleats_dir\/(.+)/;
		chomp $id;
		if($users_bleats =~ /$id/) {
				$total_bleats++;
				next if $total_bleats <= $start || $total_bleats > $end;
				open my $g, $id_path or die "couldn't open $id_path\n";
				my $details = join(' ', <$g>);
				my ($bleat) = $details =~ /bleat: (.+)/;
				my ($epoch) = $details =~ /time: (.+)/;
				my $converted_time = convert_time($epoch);
				$tweet_html .= tweet_widget($bleat, $user_to_show, $id, $converted_time);
		}
	}

	my $pagers = create_pagination($total_bleats);

    return <<eof;

      <div class="row" style="margin-top: 1em;">
		<hr/>
        <div class="large-3 columns">
			<div class="panel" style="margin-bottom:1em;">
				<div class="panel-body" style="background-color:#E6E6E6; padding-left:25px; padding-right:25px;">
					<img src="$picture_path" alt="no profile pic" style="border-style:3px solid #FFFFFF;border-radius:2px;"/>
				</div>
			</div>

			<div class="panel panel-primary" style="border-radius:2px;border-color:#ffffff">
			  <div class="panel-heading" style="border-radius:2px;>
				<h3 class="panel-title">$user_to_show</h3>
			  </div>
			  <div class="panel-body" style="background-color:#E6E6E6;">
					<b>Fullname:</b> $full_name<hr/>
					<b>About Me:</b> $about
			  </div>
			</div>
			$listen_button_html
        </div>


        	<!-- middle column feed-->
        <div class="large-6 columns" style="background-color:#FFFFFF; padding-top: 1em;">

		<!--start info about hime-->
		$tweet_html

     	<!-- this div closes the feed list-->
		     <ul class="inline-list">
					$pagers
			 </ul>
        </div>

        <aside class="large-3 columns hide-for-small">
          <!--p-->
			<div style="background-color:#E6E6E6; padding:1em; margin-bottom:1em;">
				<cite title="$home_suburb"><i class="glyphicon glyphicon-map-marker"> $home_suburb
                	</i></cite>
			</div>
			<div style="background-color:#E6E6E6; padding:1em; margin-bottom:1em">
				<b>Listens to</b><br>
				$listens_to
           	</div>
		  <!--/p-->
          <p><img src="http://placehold.it/300x440&text=[ad]"/></p>
        </aside>

      </div>


      <footer class="row">
        <div class="large-12 columns">
          <hr/>
          <div class="row">
            <div class="large-5 columns">
              <p>© Bitter</p>
            </div>
            <div class="large-7 columns">

            </div>
          </div>
        </div>
      </footer>
eof
}

#-------------------------------
# GIVES HTML DIV FOR A USER WHEN SEARCHED FOR
# param: username
#-------------------------------
sub user_widget_template {
	my $username = $_[0];
	my $full_name = "unknown";
	if(exists $bleat_account_details{$username}{"full_name"}) {
		$full_name = $bleat_account_details{$username}{"full_name"};
	}

	my $home_suburb = $bleat_account_details{$username}{"home_suburb"} || "unknown";
	my $picture_path = "$users_dir/$username/profile.jpg";
	if(!-e $picture_path) {
		$picture_path = "http://placehold.it/80x80&text=[img]";
	}

	return<<eof
	<div class="col-xs-12 col-sm-6 col-md-6">
            <div class="well well-sm">
                <div class="row">
                    <div class="col-sm-6 col-md-4">
                        <img src="$picture_path" alt="no profile pic" class="img-rounded img-responsive" />
                    </div>
                    <div class="col-sm-6 col-md-8">
                        <h4><a onclick="give_profile_search('$username')" href="javascript:void(0);">$username</a></h4>
                        <cite title="$home_suburb"><i class="glyphicon glyphicon-map-marker">
                        </i></cite> $home_suburb

                        <p>

                            <b>Full Name</b> $full_name
							<br/></p>
                        <!-- Split button -->
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary" onclick="give_profile_search('$username')">View Profile</button>
                        </div>
                    </div>
                </div>
            </div>
		</div>
eof
}


#----------------------
# List of javascript functions used
#-------------------------------
sub java_scripts {
	return<<eof;
	<script>

		function give_profile_search(username) {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			if(typeof profile_form.elements['user_profile']==='undefined') {
				var input = document.createElement('input');
				input.setAttribute('name','user_profile');
				input.setAttribute('type','hidden');
				input.setAttribute('value',username);
				profile_form.appendChild(input);
			} else {
				profile_form.elements['user_profile'].value=username;
			}
			document.getElementById('nav_status').value='profile';
			document.getElementById('basic_form').submit();
			return false;
		}

		function add_listen(listen_to_user) {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			if(typeof profile_form.elements['listen_to']==='undefined') {
				var input = document.createElement('input');
				input.setAttribute('name','listen_to');
				input.setAttribute('type','hidden');
				input.setAttribute('value',listen_to_user);
				profile_form.appendChild(input);
			} else {
				profile_form.elements['listen_to'].setAttribute('value',listen_to_user);
			}
			var save_user = document.createElement('input');
			save_user.setAttribute('name','user_profile');
			save_user.setAttribute('value',listen_to_user);
			profile_form.appendChild(input);
			<!--document.getElementById('nav_status').value='profile'-->
			return false;
		}

		function view_responses(bleat_id) {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			if(typeof profile_form.elements['tweet_id']==='undefined') {
				var input = document.createElement('input');
				input.setAttribute('name','tweet_id');
				input.setAttribute('type','hidden');
				input.setAttribute('value',bleat_id);
				profile_form.appendChild(input);
			} else {
				profile_form.elements['tweet_id'].value=bleat_id;
			}
			document.getElementById('nav_status').value='view_responses';
			document.getElementById('basic_form').submit();
			return false;
		}

		function delete_tweet(bleat_id,user_profile,page_num) {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			if(typeof profile_form.elements['tweet_id']==='undefined') {
				var input = document.createElement('input');
				input.setAttribute('name','tweet_id');
				input.setAttribute('type','hidden');
				input.setAttribute('value',bleat_id);
				profile_form.appendChild(input);
			} else {
				profile_form.elements['tweet_id'].value=bleat_id;
			}

			if(typeof profile_form.elements['action']==='undefined') {
				var input2 = document.createElement('input');
				input2.setAttribute('name','action');
				input2.setAttribute('type','hidden');
				input2.setAttribute('value','delete');
				profile_form.appendChild(input2);
			} else {
				profile_form.elements['action'].value='delete';
			}

			if(typeof profile_form.elements['user_profile']==='undefined') {
				var input3 = document.createElement('input');
				input3.setAttribute('name','user_profile');
				input3.setAttribute('type','hidden');
				input3.setAttribute('value',user_profile);
				profile_form.appendChild(input3);
			} else {
				profile_form.elements['user_profile'].value=user_profile;
			}

			if(page_num >= 0) {
				var input4 = document.createElement('input');
				input4.setAttribute('name','page_num');
				input4.setAttribute('type','hidden');
				input4.setAttribute('value',page_num);
				profile_form.appendChild(input4);
			}

			document.getElementById('basic_form').submit();
			return false;
		}

		function edit_profile() {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			document.getElementById('nav_status').value='edit_profile';
			document.getElementById('basic_form').submit();
			return false;
		}

		function change_nots() {
			var profile_form;
			profile_form = document.getElementById('nots_form');
			profile_form.submit();
			return false;
		}

		function get_page(num,user,key) {
			var profile_form;
			profile_form = document.getElementById('basic_form');
			if(typeof profile_form.elements['page_num']==='undefined') {
				var input = document.createElement('input');
				input.setAttribute('name','page_num');
				input.setAttribute('type','hidden');
				input.setAttribute('value',num);
				profile_form.appendChild(input);
			} else {
				profile_form.elements['page_num'].value='num';
			}

			if(typeof profile_form.elements['user_profile']==='undefined') {
				var input2 = document.createElement('input');
				input2.setAttribute('name','user_profile');
				input2.setAttribute('type','hidden');
				input2.setAttribute('value',user);
				profile_form.appendChild(input2);
			} else {
				profile_form.elements['user_profile'].value=user;
			}
				var input3 = document.createElement('input');
				input3.setAttribute('name','keyword');
				input3.setAttribute('type','hidden');
				input3.setAttribute('value',key);
				profile_form.appendChild(input3);

			document.getElementById('basic_form').submit();
			return false;
		}
	</script>
eof
}

#-------------------------------
# Template to the homes creen
#-------------------------------
sub home_screen {
	my $picture_path = "$users_dir/$variable_list{'logged_in_user'}/profile.jpg";
	if(!-e $picture_path) {
		$picture_path="http://placehold.it/80x80&text=[img]";
	}
	my $nav_status = $variable_list{"nav_status"};
	my $username = $variable_list{"logged_in_user"};
	my $password = $variable_list{"logged_in_password"};
	my $html_bleat = get_bleats();
	#my $html_user_widget = user_widget_template($username);

    return <<eof;

      <div class="row" style="margin-top:1em;">
        <div class="large-3 columns ">
			<div class="panel" style="margin-bottom:1em;">
				<div class="panel-body" style="background-color:#E6E6E6; padding-left:25px; padding-right:25px;">
					<img src="$picture_path" alt="no profile pic" style="border-style:3px solid #FFFFFF;border-radius:2px;"/>
				</div>
			</div>

			<div class="panel panel-primary" style="border-radius:2px;border-color:#ffffff">
			  <div class="panel-heading" style="border-radius:2px;>
				<h3 class="panel-title">Bitter</h3>
			  </div>
			  <div class="panel-body" style="background-color:#E6E6E6;">
					$username
			  </div>
			</div>
        </div>


        	<!-- middle column feed-->
        <div class="large-6 columns" style="background-color:#ffffff; padding-top: 1em;">

			<!-- START TWEET BAR/FORM-->
			<div class="row">
		 		<div class="large-2 columns small-3" style="padding-top: 5px"><b>Share Bleat</b></div>

			    <div class="large-10 columns">
					<form class="navbar-form" id="tweet" method="POST">
						<input type="hidden" name="logged_in_user" value=$username form="tweet">
						<input type="hidden" name="logged_in_password" value="$password" form="tweet">
						<input type="hidden" name="nav_status" value="$nav_status" form="tweet">
						<div class="form-group">
							<input type="text" name="tweet" placeholder="max. 142 characters" class="form-control" maxlength="142">
						</div>
						<button type="submit" name="tweetbutton" class="btn btn-primary" form="tweet"><span class="glyphicon glyphicon-pencil"></span></button>
					</form>
				</div>
			</div>
			<!-- END TWEET BAR/FORM-->
		<hr/>
		$html_bleat

     	<!-- this div closes the feed list-->

        <aside class="large-3 columns hide-for-small">
          <p><img src="http://placehold.it/300x440&text=[ad]"/></p>
        </aside>

      </div>


      <footer class="row">
        <div class="large-12 columns">
          <hr/>
          <div class="row">
            <div class="large-5 columns">
              <p>© Bitter
            </div>
            <div class="large-7 columns">
              <ul class="inline-list right">

              </ul>
            </div>
          </div>
        </div>
      </footer>
eof
}
