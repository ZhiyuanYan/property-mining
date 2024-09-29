module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [14:0] i,
    output reg [14:0] j
);


    always@(posedge clk) begin
        $display("i: %b, j: %b", i, j);
    end        
    always @(posedge clk) begin
        if(rst)begin
            i<=1;
            j<=1000;
        end
        else begin
            if(selector&&(j>=i))begin
                i <= i + 2;
                j <= j - 1;
            end
            else begin
                i  <= i;
                j <= j;
            end
        end
    end
    // assert property (!((i>j)&&(j!=666)));
endmodule