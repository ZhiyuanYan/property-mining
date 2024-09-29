module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] a,
    output reg [10:0] b,
    output reg [10:0] res,
    output reg [10:0] cnt
);


    always@(posedge clk) begin
        $display("a: %b, b: %b, res: %b, cnt: %b", a, b, res, cnt);
    end 
    
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
    
    // assert property ((cnt>0)||(res==a+b));
endmodule