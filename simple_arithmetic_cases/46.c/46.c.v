module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] c,
    output reg [10:0] n
);



    
    always @(posedge clk) begin
        if(rst)begin
            c<=0;
            n<=200;
        end
        else begin
            if(selector&&(c != n))begin
                c <= c+1;
                n <= n;
            end
            else if(selector&&(c == n))begin
                c <= 1;
                n <= n;
            end
            else begin
                c <= c;
                n <= n;
            end
        end
    end
    assert property (!((c>n)));
endmodule