module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [7:0] x,
    output reg [7:0] y,
    output reg [7:0] size
);


    
    always @(posedge clk) begin
        if(rst)begin 
            x <= 1;
            y <= 0;
            size <= 230;
        end else begin
            if((selector)&&(x<=size))begin
                x<= x + 1;
                y <= y + 1;
                size<=size;
            end
            else begin
                x<=x;
                y<=y;
                size<=size;
            end
        
        end
        
    end
    assert property (!((y!=0)&&(y!=size)&&(x>size)));
endmodule