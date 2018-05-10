
module cart
  (
   input clk,
   input rst,
   dti.consumer din0, // u1 (1)
   dti.consumer din1, // [u4] (5)
   dti.producer dout // [(u1, u4)] (6)

   );
   typedef struct packed { // u1
      logic [0:0] data; // u1
   } din0_t;

   typedef struct packed { // [u4]
      logic [0:0] eot; // u1
      logic [3:0] data; // u4
   } din1_t;

   typedef struct packed { // [(u1, u4)]
      logic [0:0] eot; // u1
      logic [4:0] data; // u5
   } dout_t;


   din0_t din0_s;
   din1_t din1_s;
   dout_t dout_s;

   assign din0_s = din0.data;
   assign din1_s = din1.data;

   assign dout_s.eot = { din1_s.eot };
   assign dout_s.data = { din1_s.data, din0_s.data };

   logic          handshake;
   assign dout.valid = din0.valid & din1.valid;
   assign handshake = dout.valid && dout.ready;
   assign dout.data = dout_s;

   assign din0.ready = handshake && (&din1_s.eot);
   assign din1.ready = handshake;



endmodule
