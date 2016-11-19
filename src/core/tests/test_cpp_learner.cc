#include <string.h>
#include "zmq.h"

int main()
{
   // This is an example of a silly learner that always replies with '.'
   char reply[1];
   int n = 0;
   const char* response = "00101110";  // '.' utf-8 code

   // connect
   void *context = zmq_ctx_new();
   void *to_env = zmq_socket(context, ZMQ_PAIR);
   int rc = zmq_connect(to_env, "tcp://localhost:5556");

   // handshake
   zmq_send(to_env, "hello", 5, 0);

   // talk
   while (true)
   {
      // acknowledge reward
      zmq_recv(to_env, reply, 1, 0);

      // acknowledge teacher/env
      zmq_recv(to_env, reply, 1, 0);

      // reply
      reply[0] = response[n % strlen(response)];
      zmq_send(to_env, reply, 1, 0);
      n += 1;
   }

   zmq_close(to_env);
   zmq_ctx_destroy(context);

   return 0;
}
