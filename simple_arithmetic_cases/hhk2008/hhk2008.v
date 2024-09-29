module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [16:0] a,
    output reg [16:0] b,
    output reg [16:0] res,
    output reg [16:0] cnt
);



    
    always @(posedge clk) begin
        if(rst)begin
            a<=300;
            b<=200;
            res<=300;
            cnt<=200;
        end
        else begin
                
                if (cnt>0) begin
                    cnt <= cnt -1;
                    res <=res+1;
                    a<=a;
                    b<=b;
                end
            end
        end
    
    assert property ((cnt>0)||(res==a+b));
endmodule