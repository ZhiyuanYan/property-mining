module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] x,
    output reg [10:0] y
);

    always@(posedge clk) begin
        $display("x: %b, y: %b", x, y);
    end 

    
    always @(posedge clk) begin
        if(rst)begin
            x<=2;
            y<=1;
        end
        else begin
                if (x<200) begin
                    x<=x+2;
                    y<=y+2;
                end
                else begin
                    x<=x;
                    y<=y;
                end
            end
        end
    
    // assert property ((x!=4)||(y!=0));
endmodule