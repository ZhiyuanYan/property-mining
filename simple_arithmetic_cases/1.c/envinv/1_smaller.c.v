module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [14:0] x,
    output reg [14:0] y,
);
    // reg [9:0] x;
    // reg [9:0] y;

    
    always @(posedge clk) begin
        if(rst)begin
            x<=1;
            y<=0;
        end
        else begin
            if(selector&&(y<200))begin
                x <= x + y;
                y <= y + 1;
            end
            else begin
                x  <= x;
                y <= y;
            end
        end
    end
    // assert property (!((y>=200)&&(x<y)));
endmodule