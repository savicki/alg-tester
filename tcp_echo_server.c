
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <error.h>
#include <errno.h>
#include <fcntl.h>
#include <strings.h>
#include <arpa/inet.h>

#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_RESET   "\x1b[0m"


int main( int argc, char *argv[] )
{
     int res, i;
     int no_reply = 0, local_port = 0;     


     for(i = 1; i < argc; i++) {
          //printf("argv [%d of %d] : '%s' \n", i, argc, argv[i]);
          char *name = argv[i];

          if (strcasecmp(name, "-noreply") == 0 || strcasecmp(name, "-no_reply") == 0) {
               no_reply = 1;
          }
          else if (strcasecmp(name, "-port") == 0) {
               if (i + 1 == argc) {
                    printf("invalid '-port' argument, port value missed, valid example '-port 5060'. Exit\n");
                    goto exit;
               }

               local_port = atoi(argv[i+1]);

               if (local_port <= 0) {
                    printf("invalid '-port' value '%s', valid example '-port 5060'. Exit\n", argv[i+1]);
                    goto exit;
               }

               i++;
          }

          //printf("Exit: argv [%d of %d] : '%s' \n", i, argc, argv[i]);
     }

     if (local_port) {
          printf("TCP port to listen on: %d \n", local_port);
     }
     else {
          printf("missed '-port' argument, valid example '-port 5060'. Exit\n");
          goto exit;
     }

     printf("no reply mode: %s \n", (no_reply) ? "ON" : "OFF");

     int sockfd = socket(AF_INET, SOCK_STREAM, 0);

     if (sockfd < 0) {
          printf("socket create error, errno: %d. Exit\n", errno);
          goto exit;
     }

     {
          int localPort = 5060; /* local port */

          struct sockaddr_in  saddr;
          memset((void*) &saddr, 0, sizeof(saddr));

          saddr.sin_family = AF_INET;
          saddr.sin_addr.s_addr = /*0L*/INADDR_ANY;
          saddr.sin_port = htons( localPort );

          res = bind(sockfd, (const struct sockaddr* ) &saddr, sizeof(saddr));

          if (res < 0) {
               printf( "bindind failed, errno: %d. Exit\n", errno );
               goto exit;
          }
     }

     struct sockaddr_in cli_addr;
     int newsockfd;


     listen(sockfd, 2);

     printf("Listening on port %d ...\n", local_port);

     do
     {
          char *test2;
          int clilen = sizeof(cli_addr);
          newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
          if (newsockfd < 0) {
               printf( "accept failed, errno: %d. Exit\n", errno);
               goto exit;
          }

          printf("connected from %s:%u \n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));

          {
               char buffer[1025];

               int read_bytes, write_bytes;

               do {
                    read_bytes = recv(newsockfd, buffer, 1024, 0);

                    if (read_bytes > 0) {
                         buffer[read_bytes] = '\0';

                         printf("recv %d bytes: '" ANSI_COLOR_GREEN "%s" ANSI_COLOR_RESET "' \n", read_bytes, buffer);
                    }

                    if (!no_reply) {
                         write_bytes = send(newsockfd, buffer, read_bytes, 0);

                         printf("send back %d bytes \n", write_bytes);
                    }
               
               } 
               while(read_bytes);
          }

          printf("disconnected from %s:%u \n", inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));

          close(newsockfd);

     } while(1);

exit:
     if (sockfd) {
          shutdown(sockfd, SHUT_RDWR);
          close(sockfd);
     }
     
     return 0;
}