
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


int main( int argc, char *argv[] )
{
     int res;

     int sockfd = socket(AF_INET, SOCK_STREAM, 0);

     if (sockfd < 0) {
          printf("socket: res: %d, errno: %d \n", sockfd, errno);
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
               printf( "bind: res: %d, errno: %d \n", sockfd, errno );
               goto exit;
          }
     }

     struct sockaddr_in cli_addr;
     int newsockfd;


     listen(sockfd, 5);

     {
          int clilen = sizeof(cli_addr);
          newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, &clilen);
          if (newsockfd < 0) {
               printf( "accept: res: %d, errno: %d \n", sockfd, errno );
               goto exit;
          }

          printf("connected from %x : %u\n", cli_addr.sin_addr.s_addr, cli_addr.sin_port);
     }

     {
          char buffer[1025];

          int read_bytes, write_bytes;

          do {
               read_bytes = recv(newsockfd, buffer, 1024, 0);

               if (read_bytes > 0) {
                    buffer[read_bytes] = '\0';

                    printf("\n ** recv (%d bytes): '%s' \n", read_bytes, buffer);
               }

               write_bytes = send(newsockfd, buffer, read_bytes, 0);

               printf("\n ** send back %d bytes \n", write_bytes);
          
          } 
          while(read_bytes);

          close(newsockfd);
     }

exit:
     shutdown( sockfd, SHUT_RDWR );
     close( sockfd );
     
     return 0;
}