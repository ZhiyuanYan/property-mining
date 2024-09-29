module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] a,
    output reg [10:0] b,
    output reg [10:0] n,
    output reg [10:0] i
);


    
    always @(posedge clk) begin
        if(rst)begin
            n<=200;
            a<=0;
            b<=0;
            i <=0;
        end
        else begin
            if(selector&&(i<n))begin
                i <= i+1;
                a <= a+1;
                b <= b+ 2;
                n<=n;
            end
            else if(!selector&&(i<n)) begin
                i <= i+1;
                a <= a+2;
                b <= b + 1;
                n<=n;
            end
            else begin
                a <= a;
                b <= b;
                i <= i;
                n<=n;
            end
        end
    end
    assert property ((i<n)||(a+b==n+n+n));
endmodule