module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [9:0] c,
    output reg [9:0] n
);



    
    always @(posedge clk) begin
        if(rst)begin
            c<=0;
            n<=500;
        end
        else begin
            if(selector&&(c == n))begin
                c <= 1;
                n <= n;
            end
            else if(selector&&(c != n))begin
                c <= c+1;
                n <= n;
            end
            else begin
                n <= n;
                c <= c;
            end
            end
        end
    assert property (!((c>500)));
endmodule