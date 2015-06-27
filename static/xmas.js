// Shorthand for $( document ).ready()
      $(function() {
          // CONFIG
          var MODE_REFRESH_MSEC = 2000;
          
          // create buttons from command modes
          $.ajax({
            url: "/get-mode-commands",
            method: 'GET',
            success: function( data ) {
              //mode-commands
              if (data['modes']) {
                var buttonContainer = $('.mode-commands');
                $.each(data['modes'], function(modeCmd, modeName) {
                  $('<button/>',{
                    text: modeName,
                    type: 'button',
                    'class': 'mode-button btn btn-primary',
                    'modeCmd': modeCmd,
                    click: function() {
                      $.ajax({
                        url: "/command",
                        method: 'POST',
                        data: {
                          command: 'mode:'+modeCmd
                        },
                        success: function( data ) {
                          console.log("sent "+modeCmd);
                        }
                      });
                    }
                  }).appendTo('.mode-commands');
                });
              }
            }
          });

          // get and possible listplay mucis interface
          $.ajax({
            url: "/get-music",
            method: 'GET',
            success: function( data ) {
              var $musicOptionsContainer = $('.music-options');
              var $musicPlaylistContainer = $('.music-now');

              //hide music if not enabled
              if (!data['music_enabled']) {
                $musicOptionsContainer.hide();
                $musicPlaylistContainer.hide();
                return;
              }

              // otherwise generate options list
              if (data['music']) {

                // Transport Controls
                $.each(['play', 'pause', 'stop', 'next'], function(idx, action) {
                  $('<button/>',{
                    text: action,
                    type: 'button',
                    'class': 'mode-button btn btn-info',
                    click: function() {
                      $.ajax({
                        url: "/command",
                        method: 'POST',
                        data: {
                          command: 'music:'+action
                        },
                        success: function( data ) {
                          console.log("sent "+action);
                        }
                      });
                    }
                  }).appendTo('.music-transport-commands');
                });
                
                // SONGS
                $.each(data['music'], function(idx, song) {
                  // skip directories
                  if (song.directory) {
                    return;
                  }
                  // add a button
                  $('<button/>',{
                    text: song.title,
                    type: 'button',
                    'class': 'mode-button btn btn-primary',
                    click: function() {
                      $.ajax({
                        url: "/command",
                        method: 'POST',
                        data: {
                          command: 'music:add:'+song.file
                        },
                        success: function( data ) {
                          console.log("sent "+song.file);
                        }
                      });
                    }
                  }).appendTo('.music-commands');
                });
                

              }
              
              // PLAYLIST
              var updatePlaylistTimeout;
              var updatePlaylist = function() { 
                // schedule next call incase this one takes a while
                updatePlaylistTimeout = setTimeout(updatePlaylist, MODE_REFRESH_MSEC);

                console.log("begin updating playlist");
                // fetch mode and update buttons
                $.ajax({
                  url: "/get-playlist",
                  method: 'GET',
                  success: function( data ) {
                    //mode-commands
                    if (data['playlist']) {
                      // empty existing items
                      $('.now-playing').empty();
                      var playlist = data['playlist'];
                      $.each(playlist, function(idx, song){
                        $('<div/>', {
                          'class': 'playlist-item',
                          'text': song.title
                        }).appendTo('.now-playing')
                      });
                    }
                  }
                });
              };
              updatePlaylist();

              $musicOptionsContainer.show();
              $musicPlaylistContainer.show();
            }
            
          
          });     

          var getCurrentModeTimeout;
          var getCurrentMode = function() { 
            // schedule next call incase this one takes a while
            getCurrentModeTimeout = setTimeout(getCurrentMode, MODE_REFRESH_MSEC);

            console.log("begin getting mode");
            // fetch mode and update buttons
            $.ajax({
              url: "/get-current-mode",
              method: 'GET',
              success: function( data ) {
                //mode-commands
                console.log("get result: ".data);
                if (data['mode']) {
                  var mode = data['mode'];
                  // find the right button
                  var $button = $('.mode-commands button.mode-button[modeCmd='+mode+']');
                  console.log("new mode button: ", $button);
                  if ($button.length > 0) {
                    console.log("button got length")
                    // deactivate other active buttons
                    $('.mode-commands button.mode-button').addClass('btn-primary').removeClass('btn-success');
                    // activate this one
                    $button.addClass('btn-success').removeClass('btn-primary');
                  }
                }
              }
            });
          };
          getCurrentMode();

      });